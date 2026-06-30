"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { wsUrl } from "@/lib/api";
import type { RecognitionMessage } from "@/lib/types";

const FRAME_INTERVAL_MS = 250;

interface Props {
  onCommit: (text: string) => void;
}

export default function WebcamRecognizer({ onCommit }: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const timerRef = useRef<number | null>(null);

  const [active, setActive] = useState(false);
  const [status, setStatus] = useState("idle");
  const [sign, setSign] = useState<string | null>(null);
  const [confidence, setConfidence] = useState(0);
  const [sentence, setSentence] = useState("");
  const [currentWord, setCurrentWord] = useState("");

  const sendFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ws = wsRef.current;
    if (!video || !canvas || !ws || ws.readyState !== WebSocket.OPEN) return;
    if (video.videoWidth === 0) return;

    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    ws.send(canvas.toDataURL("image/jpeg", 0.6));
  }, []);

  const start = useCallback(async () => {
    setStatus("requesting camera…");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }

      const ws = new WebSocket(wsUrl("/ws/recognize"));
      wsRef.current = ws;
      ws.onopen = () => {
        setStatus("recognizing");
        timerRef.current = window.setInterval(sendFrame, FRAME_INTERVAL_MS);
      };
      ws.onmessage = (e) => {
        const msg: RecognitionMessage = JSON.parse(e.data);
        setSign(msg.sign);
        setConfidence(msg.confidence);
        setSentence(msg.state.sentence);
        setCurrentWord(msg.state.current_word);
      };
      ws.onclose = () => setStatus("disconnected");
      ws.onerror = () => setStatus("error");
      setActive(true);
    } catch {
      setStatus("camera denied");
    }
  }, [sendFrame]);

  const stop = useCallback(() => {
    if (timerRef.current) window.clearInterval(timerRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    const stream = videoRef.current?.srcObject as MediaStream | null;
    stream?.getTracks().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setActive(false);
    setStatus("idle");
  }, []);

  useEffect(() => () => stop(), [stop]);

  const commit = () => {
    const text = sentence.trim();
    if (!text) return;
    onCommit(text);
    setSentence("");
    setCurrentWord("");
  };

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-800/60 p-4">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-semibold text-slate-100">Sign → Text</h3>
        <span className="text-xs text-slate-400">{status}</span>
      </div>

      <div className="relative overflow-hidden rounded-lg bg-black">
        <video ref={videoRef} className="h-56 w-full object-cover" muted playsInline />
        <canvas ref={canvasRef} className="hidden" />
        {sign && sign !== "NOTHING" && (
          <div className="absolute left-2 top-2 rounded bg-brand px-2 py-1 text-sm font-bold text-white">
            {sign} · {(confidence * 100).toFixed(0)}%
          </div>
        )}
      </div>

      <div className="mt-3 min-h-[3rem] rounded-lg bg-slate-900 p-3">
        <span className="text-slate-100">{sentence}</span>
        {currentWord && <span className="text-brand"> {currentWord}</span>}
        {!sentence && !currentWord && (
          <span className="text-slate-500">Signed text appears here…</span>
        )}
      </div>

      <div className="mt-3 flex gap-2">
        {!active ? (
          <button
            onClick={start}
            className="flex-1 rounded-lg bg-brand px-3 py-2 font-medium text-white hover:bg-brand-dark"
          >
            Start camera
          </button>
        ) : (
          <button
            onClick={stop}
            className="rounded-lg bg-slate-700 px-3 py-2 font-medium text-slate-100 hover:bg-slate-600"
          >
            Stop
          </button>
        )}
        <button
          onClick={commit}
          disabled={!sentence.trim()}
          className="flex-1 rounded-lg bg-emerald-600 px-3 py-2 font-medium text-white hover:bg-emerald-500 disabled:opacity-40"
        >
          Send to meeting
        </button>
      </div>
    </div>
  );
}
