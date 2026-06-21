import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from app.core.config import settings
from app.core.database import connect_db, disconnect_db
from app.core.logging import setup_logging
from app.api.routes import meetings, transcripts, summaries, health
from app.api.websocket.recognition import recognition_ws
from app.api.websocket.speech import speech_ws
from app.services.room_manager import sio

os.makedirs("logs", exist_ok=True)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()


fastapi_app = FastAPI(
    title="SignWave Meeting API",
    version="2.0.0",
    lifespan=lifespan,
)

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fastapi_app.include_router(health.router)
fastapi_app.include_router(meetings.router, prefix="/api")
fastapi_app.include_router(transcripts.router, prefix="/api")
fastapi_app.include_router(summaries.router, prefix="/api")

fastapi_app.add_api_websocket_route("/ws/recognize", recognition_ws)
fastapi_app.add_api_websocket_route("/ws/speech", speech_ws)

# Mount Socket.io alongside FastAPI
socket_app = socketio.ASGIApp(sio, other_asgi_app=fastapi_app)
app = socket_app
