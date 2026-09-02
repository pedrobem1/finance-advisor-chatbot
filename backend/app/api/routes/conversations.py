from uuid import UUID

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.client_identity import require_browser_client_id
from app.conversations.repository import ConversationStoreError, get_conversation_store
from app.conversations.sessions import create_conversation_session
from app.schemas.conversation import ConversationDetail, ConversationSummary


router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=list[ConversationSummary])
def list_conversations(client_id: Annotated[UUID, Depends(require_browser_client_id)]) -> list[ConversationSummary]:
    try:
        return get_conversation_store().list_conversations(client_id)
    except ConversationStoreError as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel listar as conversas.") from error


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: UUID,
    client_id: Annotated[UUID, Depends(require_browser_client_id)],
) -> ConversationDetail:
    try:
        conversation = get_conversation_store().get_conversation(client_id, conversation_id)
    except ConversationStoreError as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel abrir a conversa.") from error

    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada.")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
async def delete_conversation(
    conversation_id: UUID,
    client_id: Annotated[UUID, Depends(require_browser_client_id)],
) -> Response:
    store = get_conversation_store()
    try:
        if store.get_conversation(client_id, conversation_id) is None:
            raise HTTPException(status_code=404, detail="Conversa nao encontrada.")
    except ConversationStoreError as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel excluir a conversa.") from error

    try:
        session = create_conversation_session(conversation_id)
        try:
            await session.clear_session()
        finally:
            session.close()
        store.delete_conversation(client_id, conversation_id)
    except ConversationStoreError as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel excluir a conversa.") from error
    except Exception as error:
        raise HTTPException(status_code=503, detail="Nao foi possivel limpar o historico da conversa.") from error

    return Response(status_code=204)
