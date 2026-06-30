"use client";

import { useEffect, useRef } from "react";
import type { TranscriptLine } from "@/lib/types";

interface Props {
  lines: TranscriptLine[];
}

export default function TranscriptPanel({ lines }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [lines]);

  return (
    <div className="flex h-full flex-col rounded-xl border border-slate-700 bg-slate-800/60">
      <div className="border-b border-slate-700 px-4 py-3">
        <h3 className="font-semibold text-slate-100">Live transcript</h3>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {lines.length === 0 && (
          <p className="text-sm text-slate-500">No messages yet.</p>
        )}
        {lines.map((l) => (
          <div key={l.id} className="text-sm">
            <div className="flex items-center gap-2">
              <span className="font-medium text-slate-100">{l.speaker_name}</span>
              <span
                className={`rounded px-1.5 py-0.5 text-[10px] uppercase ${
                  l.source === "sign"
                    ? "bg-brand/20 text-brand"
                    : "bg-emerald-500/20 text-emerald-400"
                }`}
              >
                {l.source}
              </span>
              <span className="text-[10px] text-slate-500">
                {new Date(l.timestamp).toLocaleTimeString()}
              </span>
            </div>
            <p className="text-slate-300">{l.text}</p>
          </div>
        ))}
        <div ref={endRef} />
      </div>
    </div>
  );
}
