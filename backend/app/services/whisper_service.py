import asyncio
import tempfile
import os
from pathlib import Path
from typing import Optional
from loguru import logger
from app.core.config import settings


class WhisperService:
    def __init__(self):
        self._model = None
        self._lock = asyncio.Lock()

    def _ensure_loaded(self):
        if self._model is None:
            import whisper
            logger.info(f"Loading Whisper model: {settings.whisper_model}")
            self._model = whisper.load_model(settings.whisper_model)
            logger.info("Whisper ready")

    async def transcribe_bytes(self, audio_bytes: bytes, language: str = "en") -> Optional[str]:
        async with self._lock:
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self._transcribe_sync, audio_bytes, language)
                return result
            except Exception as e:
                logger.error(f"Whisper error: {e}")
                return None

    def _transcribe_sync(self, audio_bytes: bytes, language: str) -> str:
        self._ensure_loaded()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp_path = f.name
        try:
            result = self._model.transcribe(tmp_path, language=language, fp16=False)
            return result["text"].strip()
        finally:
            os.unlink(tmp_path)


whisper_service = WhisperService()
