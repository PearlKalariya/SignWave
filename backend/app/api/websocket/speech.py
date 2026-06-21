from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
import json
from app.services.whisper_service import whisper_service


async def speech_ws(websocket: WebSocket):
    """
    Receives binary audio chunks, returns transcribed text.
    Client sends JSON metadata first: {"speaker_id": "...", "speaker_name": "...", "meeting_id": "..."}
    Then sends binary WAV audio chunks.
    """
    await websocket.accept()
    meta: dict = {}
    logger.info("Speech WS connected")

    try:
        while True:
            msg = await websocket.receive()

            if msg["type"] == "websocket.receive":
                if "text" in msg and msg["text"]:
                    meta = json.loads(msg["text"])
                    await websocket.send_json({"status": "ready", "meta": meta})

                elif "bytes" in msg and msg["bytes"]:
                    audio_bytes = msg["bytes"]
                    text = await whisper_service.transcribe_bytes(audio_bytes)

                    if text:
                        await websocket.send_json({
                            "text": text,
                            "speaker_id": meta.get("speaker_id", "unknown"),
                            "speaker_name": meta.get("speaker_name", "Speaker"),
                            "meeting_id": meta.get("meeting_id", ""),
                            "source": "speech",
                        })

    except WebSocketDisconnect:
        logger.info("Speech WS disconnected")
    except Exception as e:
        logger.error(f"Speech WS error: {e}")
        await websocket.close(code=1011)
