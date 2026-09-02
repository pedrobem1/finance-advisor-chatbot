import logging
from functools import lru_cache
from typing import Annotated
from uuid import UUID, uuid4

from agents.exceptions import (
    AgentsException,
    InputGuardrailTripwireTriggered,
    MaxTurnsExceeded,
    ModelTimeoutError,
)
from fastapi import APIRouter, Depends, HTTPException, Request
from openai import APIConnectionError, APITimeoutError, AuthenticationError, OpenAIError, RateLimitError

from app.agents.master_agent import run_master_agent
from app.api.client_identity import require_browser_client_id
from app.conversations.repository import ConversationStoreError, get_conversation_store
from app.core.config import get_openai_api_key, get_settings
from app.core.rate_limit import SlidingWindowRateLimiter
from app.rag.retriever import RAGError
from app.schemas.chat import ChatRequest, ChatResponse
from app.tools.market_data import MarketDataError

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)


class AIConfigurationError(Exception):
    """Raised when the application does not have an OpenAI API key."""


class ChatRateLimitExceeded(Exception):
    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds


@lru_cache
def get_chat_rate_limiter() -> SlidingWindowRateLimiter:
    settings = get_settings()
    return SlidingWindowRateLimiter(
        max_requests=settings.chat_rate_limit_requests,
        window_seconds=settings.chat_rate_limit_window_seconds,
    )


def get_rate_limit_client_id(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def enforce_chat_rate_limit(request: Request) -> None:
    result = get_chat_rate_limiter().check(get_rate_limit_client_id(request))
    if not result.allowed:
        raise ChatRateLimitExceeded(result.retry_after_seconds)


def chat_error_response(error: Exception) -> HTTPException:
    logger.warning("Chat request failed with %s", type(error).__name__)

    if isinstance(error, (AIConfigurationError, AuthenticationError)):
        return HTTPException(
            status_code=503,
            detail={
                "code": "ai_configuration_error",
                "message": "O servico de IA nao esta configurado corretamente.",
            },
        )
    if isinstance(error, ChatRateLimitExceeded):
        return HTTPException(
            status_code=429,
            detail={
                "code": "chat_rate_limited",
                "message": "Voce enviou muitas mensagens. Tente novamente em instantes.",
            },
            headers={"Retry-After": str(error.retry_after_seconds)},
        )
    if isinstance(error, InputGuardrailTripwireTriggered):
        return HTTPException(
            status_code=400,
            detail={
                "code": "out_of_scope",
                "message": "Posso ajudar com finanças, investimentos, mercado e economia.",
            },
        )
    if isinstance(error, RateLimitError):
        return HTTPException(
            status_code=429,
            detail={
                "code": "ai_rate_limited",
                "message": "O servico de IA esta com muitas solicitacoes. Tente novamente em instantes.",
            },
        )
    if isinstance(error, (APITimeoutError, APIConnectionError, ModelTimeoutError)):
        return HTTPException(
            status_code=503,
            detail={
                "code": "ai_unavailable",
                "message": "O servico de IA esta indisponivel no momento. Tente novamente em instantes.",
            },
        )
    if isinstance(error, MaxTurnsExceeded):
        return HTTPException(
            status_code=503,
            detail={
                "code": "agent_limit_reached",
                "message": "Nao consegui concluir essa analise agora. Tente reformular a pergunta.",
            },
        )
    if isinstance(error, MarketDataError):
        return HTTPException(
            status_code=503,
            detail={
                "code": "market_data_unavailable",
                "message": "Os dados de mercado estao indisponiveis no momento. Tente novamente em instantes.",
            },
        )
    if isinstance(error, RAGError):
        return HTTPException(
            status_code=503,
            detail={
                "code": "knowledge_base_unavailable",
                "message": "A base de conhecimento esta indisponivel no momento. Tente novamente em instantes.",
            },
        )
    if isinstance(error, ConversationStoreError):
        return HTTPException(
            status_code=503,
            detail={
                "code": "conversation_store_unavailable",
                "message": "Nao foi possivel salvar a conversa. Tente novamente em instantes.",
            },
        )
    return HTTPException(
        status_code=502,
        detail={
            "code": "agent_execution_error",
            "message": "Nao foi possivel concluir sua pergunta agora. Tente novamente em instantes.",
        },
    )


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    client_id: Annotated[UUID, Depends(require_browser_client_id)],
) -> ChatResponse:
    if not get_openai_api_key():
        raise chat_error_response(AIConfigurationError())

    try:
        enforce_chat_rate_limit(http_request)
    except ChatRateLimitExceeded as error:
        raise chat_error_response(error) from error

    conversation_id = request.conversation_id or uuid4()
    store = get_conversation_store()

    try:
        if request.conversation_id and store.get_conversation(client_id, conversation_id) is None:
            raise HTTPException(status_code=404, detail="Conversa nao encontrada.")
        result = await run_master_agent(request.message, conversation_id)
        store.save_exchange(
            client_id=client_id,
            conversation_id=conversation_id,
            user_message=request.message,
            answer=result.answer,
            tools_used=result.tools_used,
            charts=result.charts,
            sources=result.sources,
        )
    except (
        AgentsException,
        APIConnectionError,
        APITimeoutError,
        AuthenticationError,
        MarketDataError,
        OpenAIError,
        RAGError,
        ConversationStoreError,
        InputGuardrailTripwireTriggered,
    ) as error:
        raise chat_error_response(error) from error

    return ChatResponse(
        answer=result.answer,
        agent="master_agent",
        conversation_id=conversation_id,
        suggested_questions=result.suggested_questions,
        tools_used=result.tools_used,
        charts=result.charts,
        sources=result.sources,
    )
