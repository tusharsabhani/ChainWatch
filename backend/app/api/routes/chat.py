from __future__ import annotations

from fastapi import APIRouter, Request

from app.api.dependencies import get_chat_service
from app.api.errors import error_response
from app.schemas.chat import ChatContextScope
from app.schemas.chat_api import (
    ChatCreateSessionRequest,
    ChatCreateSessionResponse,
    ChatMessageItem,
    ChatMessagesResponse,
    ChatPostMessageRequest,
    ChatPostMessageResponse,
    ChatSessionHeader,
    ChatSessionListItem,
    ChatSessionsResponse,
)

router = APIRouter(prefix="/chat")


def _message_to_api(message) -> ChatMessageItem:
    return ChatMessageItem(
        id=message.id,
        role=message.role.value,
        message_text=message.message_text,
        citations=[
            {
                "title": citation.title,
                "url": citation.url,
                "sourceName": citation.source_name,
                "snippet": citation.snippet,
            }
            for citation in message.citations
        ] or None,
        used_agents=message.used_agents or None,
        limitations=message.limitations or None,
        created_at=message.created_at,
    )


@router.get("/sessions", response_model=ChatSessionsResponse)
def get_chat_sessions(request: Request) -> ChatSessionsResponse:
    try:
        service = get_chat_service(request)
        sessions = service.list_sessions()
        return ChatSessionsResponse(
            items=[
                ChatSessionListItem(
                    id=session.id,
                    title=session.title,
                    context_scope=session.context_scope.value,
                    context_id=session.context_id,
                    updated_at=session.updated_at,
                )
                for session in sessions
            ]
        )
    except Exception as exc:
        return error_response(500, "chat_sessions_unavailable", str(exc))


@router.post("/sessions", response_model=ChatCreateSessionResponse)
def create_chat_session(
    request: Request,
    payload: ChatCreateSessionRequest,
) -> ChatCreateSessionResponse:
    try:
        context_scope = ChatContextScope(payload.context_scope)
    except ValueError:
        return error_response(
            400,
            "invalid_context_scope",
            f"Unsupported context scope: {payload.context_scope}",
        )

    try:
        service = get_chat_service(request)
        session = service.create_session(
            title=payload.title,
            context_scope=context_scope,
            context_id=payload.context_id,
        )
        return ChatCreateSessionResponse(
            id=session.id,
            title=session.title,
            context_scope=session.context_scope.value,
            context_id=session.context_id,
            created_at=session.created_at,
        )
    except Exception as exc:
        return error_response(500, "chat_session_create_failed", str(exc))


@router.get("/sessions/{session_id}/messages", response_model=ChatMessagesResponse)
def get_chat_messages(request: Request, session_id: str) -> ChatMessagesResponse:
    try:
        service = get_chat_service(request)
        conversation = service.get_conversation(session_id)
        return ChatMessagesResponse(
            session=ChatSessionHeader(
                id=conversation.session.id,
                title=conversation.session.title,
            ),
            messages=[_message_to_api(message) for message in conversation.messages],
        )
    except ValueError as exc:
        return error_response(404, "chat_session_not_found", str(exc))
    except Exception as exc:
        return error_response(500, "chat_processing_failed", str(exc))


@router.post("/messages", response_model=ChatPostMessageResponse)
def post_chat_message(
    request: Request,
    payload: ChatPostMessageRequest,
) -> ChatPostMessageResponse:
    try:
        service = get_chat_service(request)
        result = service.send_message(
            session_id=payload.session_id,
            message=payload.message,
        )
        return ChatPostMessageResponse(
            user_message=_message_to_api(result.user_message),
            assistant_message=_message_to_api(result.assistant_message),
        )
    except ValueError as exc:
        return error_response(404, "chat_session_not_found", str(exc))
    except Exception as exc:
        return error_response(500, "chat_processing_failed", str(exc))
