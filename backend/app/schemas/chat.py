from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.schemas.agents import AgentRunStatus, Citation


class ChatContextScope(StrEnum):
    GLOBAL = "global"
    PRODUCT = "product"
    SUPPLIER = "supplier"
    COUNTRY = "country"


class ChatMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ChatScope(BaseModel):
    context_scope: ChatContextScope
    context_id: str | None = None


class ChatSessionCreate(BaseModel):
    title: str | None = None
    context_scope: ChatContextScope = ChatContextScope.GLOBAL
    context_id: str | None = None


class ChatSessionRecord(BaseModel):
    id: str
    title: str
    context_scope: ChatContextScope
    context_id: str | None = None
    created_at: str
    updated_at: str
    last_message_at: str


class ChatHistoryMessage(BaseModel):
    role: ChatMessageRole
    message_text: str


class ChatAgentTraceSummary(BaseModel):
    agent_name: str
    status: AgentRunStatus
    summary: str
    limitations: list[str] = Field(default_factory=list)
    data_source: str | None = None


class ChatMessageRecord(BaseModel):
    id: str
    session_id: str
    role: ChatMessageRole
    message_text: str
    citations: list[Citation] = Field(default_factory=list)
    used_agents: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    agent_trace_summary: list[ChatAgentTraceSummary] = Field(default_factory=list)
    created_at: str


class ChatConversation(BaseModel):
    session: ChatSessionRecord
    messages: list[ChatMessageRecord]


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


class ChatOrchestratorInput(BaseModel):
    session_id: str
    user_message: str
    context_scope: ChatContextScope
    context_id: str | None = None
    recent_history: list[ChatHistoryMessage] = Field(default_factory=list)


class ChatOrchestratorOutput(BaseModel):
    assistant_message: str
    used_agents: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    scope: ChatScope
    limitations: list[str] = Field(default_factory=list)
    agent_trace_summary: list[ChatAgentTraceSummary] = Field(default_factory=list)


class ChatPostResult(BaseModel):
    user_message: ChatMessageRecord
    assistant_message: ChatMessageRecord
