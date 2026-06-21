from beanie import Document
from pydantic import Field
from datetime import datetime
from typing import Optional, List


class Participant(Document):
    user_id: str
    name: str
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    left_at: Optional[datetime] = None


class Meeting(Document):
    title: str
    room_code: str = Field(unique=True)
    host_id: str
    host_name: str
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    participants: List[dict] = Field(default_factory=list)
    is_active: bool = True

    class Settings:
        name = "meetings"
