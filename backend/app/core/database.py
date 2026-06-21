from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger
from app.core.config import settings
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.models.summary import Summary
from app.models.user import User


_client: Optional[AsyncIOMotorClient] = None


async def connect_db() -> None:
    global _client
    _client = AsyncIOMotorClient(settings.mongodb_url)
    await init_beanie(
        database=_client[settings.mongodb_db_name],
        document_models=[Meeting, Transcript, Summary, User],
    )
    logger.info(f"MongoDB connected: {settings.mongodb_db_name}")


async def disconnect_db() -> None:
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB disconnected")


def get_db():
    if _client is None:
        raise RuntimeError("Database not connected")
    return _client[settings.mongodb_db_name]
