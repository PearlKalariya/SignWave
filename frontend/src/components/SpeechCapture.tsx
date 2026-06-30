"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { wsUrl } from "@/lib/api";

const CLIP_MS = 4000; // length of each audio clip sent for transcription

interface Props {
  speakerId: string;
  speakerName: string;
  meetingId: string;
  onTranscript: (text: string) => void;
}

export default function SpeechCapture({
  speakerId,
  speakerName,
  meetingId,
  onTranscript,
}: Props) {
  const wsRef = useRef<WebSocket | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const loopRef = useRef<number | null>(null);

  const [active, setActive] = useState(false);
  const [status, setStatus] = useState("idle");

  const recordClip = useCallback(() => {
    const stream = streamRef.current;
    const ws = wsRef.current;
    if (!stream || !ws || ws.readyState !== WebSocket.OPEN) return;

    const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
    recorderRef.current = rec;
    const chunks: Blob[] = [];
    rec.ondataavailable = (e) => e.data.size > 0 && chunks.push(e.data);
    rec.onstop = async () => {
      const blob = new Blob(chunks, { type: "audio/webm" });
      if (blob.size > 0 && ws.readyState === WebSocket.OPEN) {
        ws.send(await blob.arrayBuffer());
      }
    };
    rec.start();
    window.setTimeout(() => rec.state !== "inactive" && rec.stop(), CLIP_MS);
  }, []);

  const start = useCallback(async () => {
    setStatus("requesting mic…");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ws = new WebSocket(wsUrl("/ws/speech"));
      wsRef.current = ws;
      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            speaker_id: speakerId,
            speaker_name: speakerName,
            meeting_id: meetingId,
          })
        );
        setStatus("listening");
        recordClip();
        loopRef.current = window.setInterval(recordClip, CLIP_MS + 200);
      };
      ws.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.text) onTranscript(msg.text);
      };
      ws.onclose = () => setStatus("disconnected");
      ws.onerror = () => setStatus("error");
      setActive(true);
    } catch {
      setStatus("mic denied");
    }
  }, [speakerId, speakerName, meetingId, recordClip, onTranscript]);

  const stop = useCallback(() => {
    if (loopRef.current) window.clearInterval(loopRef.current);
    recorderRef.current?.state !== "inactive" && recorderRef.current?.stop();
    wsRef.current?.close();
    wsRef.current = null;
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setActive(false);
    setStatus("idle");
  }, []);

  useEffect(() => () => stop(), [stop]);

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-100">Speech → Text</h3>
        <span className="text-xs text-slate-400">{status}</span>
      </div>
      <button
        onClick={active ? stop : start}
        className={`w-full rounded-lg px-3 py-2 font-medium text-white ${
          active ? "bg-rose-600 hover:bg-rose-500" : "bg-brand hover:bg-brand-dark"
        }`}
      >
        {active ? "Stop microphone" : "Start microphone"}
      </button>
      <p className="mt-2 text-xs text-slate-500">
        Speech is transcribed in {CLIP_MS / 1000}s clips and broadcast to the room.
      </p>
    </div>
  );
}
