from __future__ import annotations

from app.schemas.common import CamelModel


class ChatSessionListItem(CamelModel):
    id: str
    title: str
    context_scope: str
    context_id: str | None = None
    updated_at: str


class ChatSessionsResponse(CamelModel):
    items: list[ChatSessionListItem]


class ChatCreateSessionRequest(CamelModel):
    title: str | None = None
    context_scope: str = "global"
    context_id: str | None = None


class ChatCreateSessionResponse(CamelModel):
    id: str
    title: str
    context_scope: str
    context_id: str | None = None
    created_at: str


class ChatSessionHeader(CamelModel):
    id: str
    title: str


class ChatCitationItem(CamelModel):
    title: str
    url: str
    source_name: str
    snippet: str | None = None


class ChatMessageItem(CamelModel):
    id: str
    role: str
    message_text: str
    citations: list[ChatCitationItem] | None = None
    used_agents: list[str] | None = None
    limitations: list[str] | None = None
    created_at: str


class ChatMessagesResponse(CamelModel):
    session: ChatSessionHeader
    messages: list[ChatMessageItem]


class ChatPostMessageRequest(CamelModel):
    session_id: str
    message: str


class ChatPostMessageResponse(CamelModel):
    user_message: ChatMessageItem
    assistant_message: ChatMessageItem
