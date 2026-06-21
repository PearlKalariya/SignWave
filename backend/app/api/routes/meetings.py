from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import random, string
from app.models.meeting import Meeting
from app.models.transcript import Transcript
from app.services.summary_service import summary_service

router = APIRouter(prefix="/meetings", tags=["meetings"])


def _room_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _out(meeting: Meeting) -> dict:
    d = meeting.model_dump()
    d["id"] = str(meeting.id)
    return d


class CreateMeetingRequest(BaseModel):
    title: str
    host_id: str
    host_name: str


class EndMeetingRequest(BaseModel):
    generate_summary: bool = True


@router.post("/")
async def create_meeting(body: CreateMeetingRequest):
    meeting = Meeting(
        title=body.title,
        room_code=_room_code(),
        host_id=body.host_id,
        host_name=body.host_name,
    )
    await meeting.insert()
    return _out(meeting)


@router.get("/")
async def list_meetings(host_id: Optional[str] = None):
    query = Meeting.find()
    if host_id:
        query = Meeting.find(Meeting.host_id == host_id)
    meetings = await query.sort("-started_at").to_list()
    return [_out(m) for m in meetings]


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    meeting = await Meeting.get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return _out(meeting)


@router.get("/room/{room_code}")
async def get_meeting_by_room(room_code: str):
    meeting = await Meeting.find_one(Meeting.room_code == room_code)
    if not meeting:
        raise HTTPException(404, "Room not found")
    return _out(meeting)


@router.post("/{meeting_id}/end")
async def end_meeting(meeting_id: str, body: EndMeetingRequest):
    meeting = await Meeting.get(meeting_id)
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    meeting.is_active = False
    meeting.ended_at = datetime.utcnow()
    await meeting.save()

    result: dict = {"meeting": _out(meeting)}
    if body.generate_summary:
        summary = await summary_service.generate_summary(meeting_id, meeting.title)
        result["summary"] = summary

    return result


@router.get("/{meeting_id}/transcripts")
async def get_transcripts(meeting_id: str):
    return await Transcript.find(
        Transcript.meeting_id == meeting_id
    ).sort("+timestamp").to_list()
