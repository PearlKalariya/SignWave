import type { Meeting, TranscriptLine, Summary } from "./types";

export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText);
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  createMeeting(body: { title: string; host_id: string; host_name: string }) {
    return fetch(`${API_BASE}/api/meetings/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then((r) => json<Meeting>(r));
  },

  listMeetings() {
    return fetch(`${API_BASE}/api/meetings/`).then((r) => json<Meeting[]>(r));
  },

  getMeetingByRoom(roomCode: string) {
    return fetch(`${API_BASE}/api/meetings/room/${roomCode}`).then((r) =>
      json<Meeting>(r)
    );
  },

  getTranscripts(meetingId: string) {
    return fetch(`${API_BASE}/api/meetings/${meetingId}/transcripts`)
      .then((r) => json<(TranscriptLine & { _id?: string })[]>(r))
      .then((rows) =>
        rows.map((row) => ({ ...row, id: row.id ?? row._id ?? crypto.randomUUID() }))
      );
  },

  endMeeting(meetingId: string, generate_summary = true) {
    return fetch(`${API_BASE}/api/meetings/${meetingId}/end`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ generate_summary }),
    }).then((r) => json<{ meeting: Meeting; summary?: Summary }>(r));
  },

  getSummary(meetingId: string) {
    return fetch(`${API_BASE}/api/summaries/${meetingId}`).then((r) =>
      json<Summary>(r)
    );
  },

  regenerateSummary(meetingId: string, title = "Meeting") {
    return fetch(
      `${API_BASE}/api/summaries/${meetingId}/regenerate?title=${encodeURIComponent(title)}`,
      { method: "POST" }
    ).then((r) => json<Summary>(r));
  },

  chat(meetingId: string, question: string) {
    return fetch(`${API_BASE}/api/summaries/${meetingId}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }).then((r) => json<{ question: string; answer: string }>(r));
  },
};

export function wsUrl(path: string): string {
  return API_BASE.replace(/^http/, "ws") + path;
}
