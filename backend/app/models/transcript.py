from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Literal


class Transcript(Document):
    meeting_id: str
    speaker_id: str
    speaker_name: str
    text: str
    source: Literal["speech", "sign"] = "speech"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence: float = 1.0

    class Settings:
        name = "transcripts"
