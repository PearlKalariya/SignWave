import anthropic
import json
from typing import List
from loguru import logger
from app.core.config import settings
from app.models.transcript import Transcript
from app.models.summary import Summary


SYSTEM_PROMPT = """You are an expert meeting analyst. Given a meeting transcript, extract structured insights.
Respond ONLY with valid JSON matching this schema:
{
  "full_summary": "2-3 sentence overview",
  "decisions": ["decision 1", "decision 2"],
  "action_items": [{"task": "...", "owner": "...", "deadline": "..."}],
  "risks": ["risk 1"],
  "participants": ["name1", "name2"]
}"""


class SummaryService:
    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key) if settings.anthropic_api_key else None

    async def generate_summary(self, meeting_id: str, meeting_title: str) -> Summary:
        transcripts: List[Transcript] = await Transcript.find(
            Transcript.meeting_id == meeting_id
        ).sort("+timestamp").to_list()

        if not transcripts:
            return await self._empty_summary(meeting_id, meeting_title)

        raw = "\n".join(
            f"[{t.timestamp.strftime('%H:%M')}] {t.speaker_name} ({t.source}): {t.text}"
            for t in transcripts
        )

        parsed = await self._call_claude(raw) if self._client else self._fallback(raw)

        summary = Summary(
            meeting_id=meeting_id,
            title=meeting_title,
            full_summary=parsed.get("full_summary", ""),
            decisions=parsed.get("decisions", []),
            action_items=parsed.get("action_items", []),
            risks=parsed.get("risks", []),
            participants=parsed.get("participants", []),
            raw_transcript=raw,
        )
        await summary.insert()
        return summary

    async def _call_claude(self, transcript: str) -> dict:
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": f"Transcript:\n{transcript}"}],
                )
            )
            return json.loads(response.content[0].text)
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return self._fallback(transcript)

    def _fallback(self, transcript: str) -> dict:
        lines = transcript.strip().split("\n")
        speakers = list({line.split("]")[-1].split(":")[0].strip() for line in lines if "]" in line})
        return {
            "full_summary": f"Meeting with {len(lines)} messages from {len(speakers)} participants.",
            "decisions": [],
            "action_items": [],
            "risks": [],
            "participants": speakers,
        }

    async def answer_question(self, transcript: str, question: str) -> str:
        if not self._client:
            return "LLM not configured. Set ANTHROPIC_API_KEY."
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=512,
                    system="You are a meeting assistant. Answer questions about the meeting transcript accurately and concisely.",
                    messages=[{
                        "role": "user",
                        "content": f"Transcript:\n{transcript}\n\nQuestion: {question}"
                    }],
                )
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude Q&A error: {e}")
            return "Could not answer at this time."

    async def _empty_summary(self, meeting_id: str, title: str) -> Summary:
        s = Summary(meeting_id=meeting_id, title=title, full_summary="No transcript available.")
        await s.insert()
        return s


summary_service = SummaryService()
