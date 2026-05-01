from __future__ import annotations

import json
from datetime import datetime, timezone

from app.db.repositories.base import SQLiteRepository
from app.schemas.chat import (
    ChatAgentTraceSummary,
    ChatContextScope,
    ChatMessageRecord,
    ChatMessageRole,
    ChatSessionRecord,
)
from app.schemas.agents import Citation


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ChatRepository(SQLiteRepository):
    def create_session(
        self,
        *,
        session_id: str,
        title: str,
        context_scope: ChatContextScope,
        context_id: str | None,
    ) -> ChatSessionRecord:
        timestamp = _utc_now_iso()
        self.execute(
            """
            INSERT INTO chat_sessions (
                id,
                title,
                context_scope,
                context_id,
                created_at,
                updated_at,
                last_message_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                title,
                context_scope.value,
                context_id,
                timestamp,
                timestamp,
                timestamp,
            ),
        )
        session = self.get_session(session_id)
        if session is None:
            raise RuntimeError(f"Chat session creation failed for {session_id}")
        return session

    def get_session(self, session_id: str) -> ChatSessionRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                title,
                context_scope,
                context_id,
                created_at,
                updated_at,
                last_message_at
            FROM chat_sessions
            WHERE id = ?
            """,
            (session_id,),
        )
        if row is None:
            return None
        return ChatSessionRecord.model_validate(dict(row))

    def list_sessions(self, *, limit: int = 20) -> list[ChatSessionRecord]:
        rows = self.fetch_all(
            """
            SELECT
                id,
                title,
                context_scope,
                context_id,
                created_at,
                updated_at,
                last_message_at
            FROM chat_sessions
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [ChatSessionRecord.model_validate(dict(row)) for row in rows]

    def update_session_title(self, *, session_id: str, title: str) -> ChatSessionRecord:
        self.execute(
            """
            UPDATE chat_sessions
            SET title = ?,
                updated_at = ?
            WHERE id = ?
            """,
            (
                title,
                _utc_now_iso(),
                session_id,
            ),
        )
        session = self.get_session(session_id)
        if session is None:
            raise RuntimeError(f"Chat session {session_id} not found after title update.")
        return session

    def touch_session(self, *, session_id: str, touched_at: str | None = None) -> ChatSessionRecord:
        timestamp = touched_at or _utc_now_iso()
        self.execute(
            """
            UPDATE chat_sessions
            SET updated_at = ?,
                last_message_at = ?
            WHERE id = ?
            """,
            (
                timestamp,
                timestamp,
                session_id,
            ),
        )
        session = self.get_session(session_id)
        if session is None:
            raise RuntimeError(f"Chat session {session_id} not found after touch.")
        return session

    def create_message(
        self,
        *,
        message_id: str,
        session_id: str,
        role: ChatMessageRole,
        message_text: str,
        citations: list[Citation] | None = None,
        used_agents: list[str] | None = None,
        limitations: list[str] | None = None,
        agent_trace_summary: list[ChatAgentTraceSummary] | None = None,
    ) -> ChatMessageRecord:
        created_at = _utc_now_iso()
        citations_json = (
            json.dumps([citation.model_dump(mode="json") for citation in citations], sort_keys=True)
            if citations
            else None
        )
        agent_trace_json = (
            json.dumps(
                {
                    "usedAgents": used_agents or [],
                    "limitations": limitations or [],
                    "agentTraceSummary": [
                        item.model_dump(mode="json") for item in (agent_trace_summary or [])
                    ],
                },
                sort_keys=True,
            )
            if used_agents or limitations or agent_trace_summary
            else None
        )
        self.execute(
            """
            INSERT INTO chat_messages (
                id,
                session_id,
                role,
                message_text,
                citations_json,
                agent_trace_json,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                session_id,
                role.value,
                message_text,
                citations_json,
                agent_trace_json,
                created_at,
            ),
        )
        message = self.get_message(message_id)
        if message is None:
            raise RuntimeError(f"Chat message creation failed for {message_id}")
        return message

    def get_message(self, message_id: str) -> ChatMessageRecord | None:
        row = self.fetch_one(
            """
            SELECT
                id,
                session_id,
                role,
                message_text,
                citations_json,
                agent_trace_json,
                created_at
            FROM chat_messages
            WHERE id = ?
            """,
            (message_id,),
        )
        if row is None:
            return None
        return self._row_to_message(dict(row))

    def list_messages(self, session_id: str) -> list[ChatMessageRecord]:
        rows = self.fetch_all(
            """
            SELECT
                id,
                session_id,
                role,
                message_text,
                citations_json,
                agent_trace_json,
                created_at
            FROM chat_messages
            WHERE session_id = ?
            ORDER BY created_at ASC, id ASC
            """,
            (session_id,),
        )
        return [self._row_to_message(dict(row)) for row in rows]

    def _row_to_message(self, row: dict[str, object]) -> ChatMessageRecord:
        citations_payload = json.loads(str(row["citations_json"])) if row["citations_json"] else []
        trace_payload = json.loads(str(row["agent_trace_json"])) if row["agent_trace_json"] else {}
        return ChatMessageRecord(
            id=str(row["id"]),
            session_id=str(row["session_id"]),
            role=ChatMessageRole(str(row["role"])),
            message_text=str(row["message_text"]),
            citations=[Citation.model_validate(item) for item in citations_payload],
            used_agents=list(trace_payload.get("usedAgents", [])),
            limitations=list(trace_payload.get("limitations", [])),
            agent_trace_summary=[
                ChatAgentTraceSummary.model_validate(item)
                for item in trace_payload.get("agentTraceSummary", [])
            ],
            created_at=str(row["created_at"]),
        )
