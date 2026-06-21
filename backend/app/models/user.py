from beanie import Document
from pydantic import EmailStr, Field
from datetime import datetime
from typing import Optional


class User(Document):
    name: str
    email: EmailStr
    avatar: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
