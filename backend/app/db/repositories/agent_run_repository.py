from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

from app.db.repositories.base import SQLiteRepository
from app.schemas.agents import AgentRunStatus, AgentTriggerType


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentRunRepository(SQLiteRepository):
    def create_run(
        self,
        *,
        run_id: str,
        agent_name: str,
        trigger_type: AgentTriggerType,
        trigger_ref: str | None,
        input_ref: str | None,
        connection: sqlite3.Connection | None = None,
    ) -> str:
        started_at = _utc_now_iso()
        self.execute(
            """
            INSERT INTO agent_runs (
                id,
                agent_name,
                trigger_type,
                trigger_ref,
                status,
                started_at,
                completed_at,
                input_ref,
                output_ref,
                error_message,
                duration_ms
            )
            VALUES (?, ?, ?, ?, ?, ?, NULL, ?, NULL, NULL, NULL)
            """,
            (
                run_id,
                agent_name,
                trigger_type.value,
                trigger_ref,
                AgentRunStatus.RUNNING.value,
                started_at,
                input_ref,
            ),
            connection=connection,
        )
        return started_at

    def finalize_run(
        self,
        *,
        run_id: str,
        status: AgentRunStatus,
        output_ref: str | None,
        error_message: str | None,
        duration_ms: int,
        connection: sqlite3.Connection | None = None,
    ) -> str:
        completed_at = _utc_now_iso()
        self.execute(
            """
            UPDATE agent_runs
            SET status = ?,
                completed_at = ?,
                output_ref = ?,
                error_message = ?,
                duration_ms = ?
            WHERE id = ?
            """,
            (
                status.value,
                completed_at,
                output_ref,
                error_message,
                duration_ms,
                run_id,
            ),
            connection=connection,
        )
        return completed_at

    def list_runs_for_agent(self, agent_name: str) -> list[sqlite3.Row]:
        return self.fetch_all(
            """
            SELECT *
            FROM agent_runs
            WHERE agent_name = ?
            ORDER BY started_at ASC
            """,
            (agent_name,),
        )
