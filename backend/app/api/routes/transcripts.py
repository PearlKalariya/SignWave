from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal, Optional
from app.models.transcript import Transcript

router = APIRouter(prefix="/transcripts", tags=["transcripts"])


class AddTranscriptRequest(BaseModel):
    meeting_id: str
    speaker_id: str
    speaker_name: str
    text: str
    source: Literal["speech", "sign"] = "speech"
    confidence: float = 1.0


@router.post("/")
async def add_transcript(body: AddTranscriptRequest):
    transcript = Transcript(**body.model_dump())
    await transcript.insert()
    return transcript


@router.get("/search")
async def search_transcripts(q: str, meeting_id: Optional[str] = None):
    query = Transcript.find({"$text": {"$search": q}})
    if meeting_id:
        query = Transcript.find(
            {"$text": {"$search": q}, "meeting_id": meeting_id}
        )
    return await query.sort("-timestamp").limit(50).to_list()
