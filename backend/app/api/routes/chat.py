from fastapi import APIRouter

from app.agents.finance_agent import run_finance_agent
from app.schemas.chat import ChatRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    answer = await run_finance_agent(request.message)

    return ChatResponse(
        answer=answer,
        agent="finance_agent",
    )
