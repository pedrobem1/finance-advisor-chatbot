from fastapi import APIRouter

from app.agents.master_agent import run_master_agent
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    result = await run_master_agent(request.message)

    return ChatResponse(
        answer=result.answer,
        agent="master_agent",
        tools_used=result.tools_used,
    )
