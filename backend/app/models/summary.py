from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import List, Optional


class ActionItem(Document):
    task: str
    owner: Optional[str] = None
    deadline: Optional[str] = None


class Summary(Document):
    meeting_id: str
    title: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    decisions: List[str] = Field(default_factory=list)
    action_items: List[dict] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    participants: List[str] = Field(default_factory=list)
    full_summary: str = ""
    raw_transcript: str = ""

    class Settings:
        name = "summaries"
