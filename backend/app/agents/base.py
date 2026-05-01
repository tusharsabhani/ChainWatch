from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from app.config import Settings
from app.db.connection import SQLiteConnectionFactory
from app.db.repositories.agent_run_repository import AgentRunRepository
from app.schemas.agents import AgentRunStatus, AgentTriggerType
from app.services.storage import StorageManager


def _serialize_payload(payload: BaseModel | dict[str, Any]) -> dict[str, Any]:
    if isinstance(payload, BaseModel):
        return payload.model_dump(mode="json")
    return payload


@dataclass(slots=True)
class AgentTraceHandle:
    run_id: str
    started_at_monotonic: float
    log_path: Path
    input_payload: dict[str, Any]
    trigger_type: AgentTriggerType
    trigger_ref: str | None


class BaseAgent:
    def __init__(
        self,
        *,
        agent_name: str,
        settings: Settings,
        storage: StorageManager,
        database: SQLiteConnectionFactory,
    ) -> None:
        self.agent_name = agent_name
        self.settings = settings
        self.storage = storage
        self.database = database
        self.agent_run_repository = AgentRunRepository(database)

    def _start_trace(
        self,
        *,
        trigger_type: AgentTriggerType,
        trigger_ref: str | None,
        input_payload: BaseModel | dict[str, Any],
    ) -> AgentTraceHandle:
        run_id = f"run_{uuid.uuid4().hex[:12]}"
        serialized_input = _serialize_payload(input_payload)
        input_ref = json.dumps(serialized_input, sort_keys=True)[:1000]
        self.agent_run_repository.create_run(
            run_id=run_id,
            agent_name=self.agent_name,
            trigger_type=trigger_type,
            trigger_ref=trigger_ref,
            input_ref=input_ref,
        )
        return AgentTraceHandle(
            run_id=run_id,
            started_at_monotonic=time.monotonic(),
            log_path=self.storage.agent_run_log_path(run_id),
            input_payload=serialized_input,
            trigger_type=trigger_type,
            trigger_ref=trigger_ref,
        )

    def _finish_trace(
        self,
        trace: AgentTraceHandle,
        *,
        status: AgentRunStatus,
        output_payload: BaseModel | dict[str, Any],
        error_message: str | None = None,
    ) -> None:
        serialized_output = _serialize_payload(output_payload)
        duration_ms = int((time.monotonic() - trace.started_at_monotonic) * 1000)
        output_ref = self.settings.to_relative_path(trace.log_path)
        self.agent_run_repository.finalize_run(
            run_id=trace.run_id,
            status=status,
            output_ref=output_ref,
            error_message=error_message,
            duration_ms=duration_ms,
        )
        log_payload = {
            "runId": trace.run_id,
            "agentName": self.agent_name,
            "triggerType": trace.trigger_type.value,
            "triggerRef": trace.trigger_ref,
            "status": status.value,
            "durationMs": duration_ms,
            "input": trace.input_payload,
            "output": serialized_output,
            "errorMessage": error_message,
        }
        self.storage.write_markdown_artifact(
            trace.log_path,
            json.dumps(log_payload, indent=2, sort_keys=True),
        )

    def _trace_status(self, *, partial: bool = False, failed: bool = False) -> AgentRunStatus:
        if failed:
            return AgentRunStatus.FAILED
        if partial:
            return AgentRunStatus.PARTIAL
        return AgentRunStatus.COMPLETED
