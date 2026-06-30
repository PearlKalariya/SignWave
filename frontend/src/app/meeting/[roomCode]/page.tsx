"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getSocket, emitSubtitle } from "@/lib/socket";
import { getUserId, getUserName } from "@/lib/identity";
import type { Meeting, TranscriptLine, Participant } from "@/lib/types";
import WebcamRecognizer from "@/components/WebcamRecognizer";
import SpeechCapture from "@/components/SpeechCapture";
import TranscriptPanel from "@/components/TranscriptPanel";

export default function MeetingRoom() {
  const router = useRouter();
  const params = useParams<{ roomCode: string }>();
  const roomCode = params.roomCode;

  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [lines, setLines] = useState<TranscriptLine[]>([]);
  const [participants, setParticipants] = useState<Participant[]>([]);
  const [error, setError] = useState("");
  const [ending, setEnding] = useState(false);

  const userId = useRef(getUserId());
  const userName = useRef(getUserName() || "Guest");

  // Load meeting + existing transcript, wire up socket.
  useEffect(() => {
    let cancelled = false;
    api
      .getMeetingByRoom(roomCode)
      .then(async (m) => {
        if (cancelled) return;
        setMeeting(m);
        const existing = await api.getTranscripts(m.id).catch(() => []);
        if (!cancelled) setLines(existing);

        const socket = getSocket();
        socket.emit("join_room", {
          room_code: roomCode,
          user_id: userId.current,
          user_name: userName.current,
        });
        socket.on("subtitle_received", (line: TranscriptLine) =>
          setLines((prev) => [...prev, line])
        );
        socket.on("participant_joined", (p: Participant) =>
          setParticipants((prev) =>
            prev.find((x) => x.user_id === p.user_id) ? prev : [...prev, p]
          )
        );
        socket.on("participant_left", (p: Participant) =>
          setParticipants((prev) => prev.filter((x) => x.user_id !== p.user_id))
        );
      })
      .catch(() => setError("Room not found."));

    return () => {
      cancelled = true;
      const socket = getSocket();
      socket.emit("leave_room", { room_code: roomCode });
      socket.off("subtitle_received");
      socket.off("participant_joined");
      socket.off("participant_left");
    };
  }, [roomCode]);

  const broadcast = useCallback(
    (text: string, source: "sign" | "speech") => {
      if (!meeting) return;
      emitSubtitle({
        room_code: roomCode,
        meeting_id: meeting.id,
        speaker_id: userId.current,
        speaker_name: userName.current,
        text,
        source,
      });
    },
    [meeting, roomCode]
  );

  const endMeeting = async () => {
    if (!meeting) return;
    setEnding(true);
    try {
      await api.endMeeting(meeting.id, true);
      router.push(`/summary/${meeting.id}`);
    } catch (e) {
      setError(String(e));
      setEnding(false);
    }
  };

  if (error) {
    return (
      <main className="mx-auto max-w-md px-6 py-20 text-center">
        <p className="mb-4 text-rose-400">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="rounded-lg bg-brand px-4 py-2 font-medium text-white"
        >
          Back to lobby
        </button>
      </main>
    );
  }

  if (!meeting) {
    return <main className="px-6 py-20 text-center text-slate-400">Loading…</main>;
  }

  const isHost = meeting.host_id === userId.current;

  return (
    <main className="mx-auto max-w-6xl px-6 py-6">
      <header className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">{meeting.title}</h1>
          <p className="text-sm text-slate-400">
            Room <span className="font-mono text-brand">{meeting.room_code}</span>
            {participants.length > 0 && (
              <span className="ml-3">· {participants.length} joined</span>
            )}
          </p>
        </div>
        {isHost ? (
          <button
            onClick={endMeeting}
            disabled={ending}
            className="rounded-lg bg-rose-600 px-4 py-2 font-medium text-white hover:bg-rose-500 disabled:opacity-50"
          >
            {ending ? "Ending…" : "End & summarize"}
          </button>
        ) : (
          <button
            onClick={() => router.push("/")}
            className="rounded-lg bg-slate-700 px-4 py-2 font-medium text-white hover:bg-slate-600"
          >
            Leave
          </button>
        )}
      </header>

      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <WebcamRecognizer onCommit={(t) => broadcast(t, "sign")} />
          <SpeechCapture
            speakerId={userId.current}
            speakerName={userName.current}
            meetingId={meeting.id}
            onTranscript={(t) => broadcast(t, "speech")}
          />
        </div>
        <div className="h-[calc(100vh-9rem)]">
          <TranscriptPanel lines={lines} />
        </div>
      </div>
    </main>
  );
}
