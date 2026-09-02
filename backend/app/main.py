from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mangum import Mangum

from app.api.routes.chat import router as chat_router
from app.api.routes.conversations import router as conversations_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(conversations_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.environment}


lambda_handler = Mangum(app, lifespan="off")
