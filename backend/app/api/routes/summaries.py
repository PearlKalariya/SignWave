from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.summary import Summary
from app.services.summary_service import summary_service

router = APIRouter(prefix="/summaries", tags=["summaries"])


class ChatRequest(BaseModel):
    question: str


@router.get("/{meeting_id}")
async def get_summary(meeting_id: str):
    summary = await Summary.find_one(Summary.meeting_id == meeting_id)
    if not summary:
        raise HTTPException(404, "Summary not found")
    return summary


@router.post("/{meeting_id}/regenerate")
async def regenerate_summary(meeting_id: str, title: str = "Meeting"):
    existing = await Summary.find_one(Summary.meeting_id == meeting_id)
    if existing:
        await existing.delete()
    return await summary_service.generate_summary(meeting_id, title)


@router.post("/{meeting_id}/chat")
async def chat_with_transcript(meeting_id: str, body: ChatRequest):
    """RAG: answer questions about a specific meeting transcript."""
    summary = await Summary.find_one(Summary.meeting_id == meeting_id)
    if not summary or not summary.raw_transcript:
        raise HTTPException(404, "No transcript available for this meeting")

    answer = await summary_service.answer_question(
        transcript=summary.raw_transcript,
        question=body.question,
    )
    return {"question": body.question, "answer": answer}
