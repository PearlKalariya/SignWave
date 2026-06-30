"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Summary } from "@/lib/types";

interface ChatTurn {
  q: string;
  a: string;
}

export default function SummaryPage() {
  const router = useRouter();
  const params = useParams<{ meetingId: string }>();
  const meetingId = params.meetingId;

  const [summary, setSummary] = useState<Summary | null>(null);
  const [error, setError] = useState("");
  const [question, setQuestion] = useState("");
  const [chat, setChat] = useState<ChatTurn[]>([]);
  const [asking, setAsking] = useState(false);

  useEffect(() => {
    api
      .getSummary(meetingId)
      .then(setSummary)
      .catch(() => setError("No summary found for this meeting yet."));
  }, [meetingId]);

  const ask = async () => {
    const q = question.trim();
    if (!q) return;
    setAsking(true);
    setQuestion("");
    try {
      const res = await api.chat(meetingId, q);
      setChat((prev) => [...prev, { q, a: res.answer }]);
    } catch (e) {
      setChat((prev) => [...prev, { q, a: `Error: ${e}` }]);
    } finally {
      setAsking(false);
    }
  };

  if (error) {
    return (
      <main className="mx-auto max-w-md px-6 py-20 text-center">
        <p className="mb-4 text-slate-400">{error}</p>
        <button
          onClick={() => router.push("/")}
          className="rounded-lg bg-brand px-4 py-2 font-medium text-white"
        >
          Back to lobby
        </button>
      </main>
    );
  }

  if (!summary) {
    return <main className="px-6 py-20 text-center text-slate-400">Loading…</main>;
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{summary.title}</h1>
          <p className="text-sm text-slate-400">
            Summary · {new Date(summary.generated_at).toLocaleString()}
          </p>
        </div>
        <button
          onClick={() => router.push("/")}
          className="rounded-lg bg-slate-700 px-4 py-2 font-medium text-white hover:bg-slate-600"
        >
          Lobby
        </button>
      </header>

      {summary.full_summary && (
        <section className="mb-6 rounded-xl border border-slate-700 bg-slate-800/60 p-5">
          <h2 className="mb-2 font-semibold">Overview</h2>
          <p className="whitespace-pre-wrap text-slate-300">{summary.full_summary}</p>
        </section>
      )}

      <div className="mb-6 grid gap-6 sm:grid-cols-2">
        <Card title="Decisions" items={summary.decisions} empty="No decisions recorded." />
        <Card title="Risks" items={summary.risks} empty="No risks flagged." />
      </div>

      <section className="mb-8 rounded-xl border border-slate-700 bg-slate-800/60 p-5">
        <h2 className="mb-3 font-semibold">Action items</h2>
        {summary.action_items.length === 0 ? (
          <p className="text-sm text-slate-500">No action items.</p>
        ) : (
          <ul className="space-y-2">
            {summary.action_items.map((a, i) => (
              <li key={i} className="rounded-lg bg-slate-900 px-3 py-2 text-sm">
                <span className="text-slate-200">{a.task}</span>
                {a.owner && <span className="ml-2 text-brand">@{a.owner}</span>}
                {a.deadline && (
                  <span className="ml-2 text-slate-500">· {a.deadline}</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
        <h2 className="mb-3 font-semibold">Ask about this meeting</h2>
        <div className="mb-3 space-y-3">
          {chat.map((t, i) => (
            <div key={i}>
              <p className="text-sm font-medium text-brand">Q: {t.q}</p>
              <p className="whitespace-pre-wrap text-sm text-slate-300">{t.a}</p>
            </div>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && ask()}
            placeholder="e.g. What did we decide about the deadline?"
            className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-brand"
          />
          <button
            onClick={ask}
            disabled={asking}
            className="rounded-lg bg-brand px-4 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {asking ? "…" : "Ask"}
          </button>
        </div>
      </section>
    </main>
  );
}

function Card({
  title,
  items,
  empty,
}: {
  title: string;
  items: string[];
  empty: string;
}) {
  return (
    <section className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
      <h2 className="mb-2 font-semibold">{title}</h2>
      {items.length === 0 ? (
        <p className="text-sm text-slate-500">{empty}</p>
      ) : (
        <ul className="list-disc space-y-1 pl-5 text-sm text-slate-300">
          {items.map((it, i) => (
            <li key={i}>{it}</li>
          ))}
        </ul>
      )}
    </section>
  );
}
