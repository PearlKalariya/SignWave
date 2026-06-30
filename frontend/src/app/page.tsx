"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getUserId, getUserName, setUserName } from "@/lib/identity";
import type { Meeting } from "@/lib/types";

export default function Lobby() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [title, setTitle] = useState("");
  const [roomCode, setRoomCode] = useState("");
  const [recent, setRecent] = useState<Meeting[]>([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    setName(getUserName());
    api.listMeetings().then(setRecent).catch(() => {});
  }, []);

  const create = async () => {
    if (!name.trim() || !title.trim()) {
      setError("Name and title are required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      setUserName(name.trim());
      const meeting = await api.createMeeting({
        title: title.trim(),
        host_id: getUserId(),
        host_name: name.trim(),
      });
      router.push(`/meeting/${meeting.room_code}`);
    } catch (e) {
      setError(String(e));
      setBusy(false);
    }
  };

  const join = () => {
    if (!name.trim() || !roomCode.trim()) {
      setError("Name and room code are required.");
      return;
    }
    setUserName(name.trim());
    router.push(`/meeting/${roomCode.trim().toUpperCase()}`);
  };

  return (
    <main className="mx-auto max-w-3xl px-6 py-12">
      <header className="mb-10 text-center">
        <h1 className="text-4xl font-bold tracking-tight">
          Sign<span className="text-brand">Wave</span>
        </h1>
        <p className="mt-2 text-slate-400">
          Inclusive meetings — sign language and speech, transcribed live.
        </p>
      </header>

      <div className="mb-6">
        <label className="mb-1 block text-sm text-slate-400">Your name</label>
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Pearl"
          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-brand"
        />
      </div>

      {error && (
        <p className="mb-4 rounded-lg bg-rose-500/10 px-3 py-2 text-sm text-rose-400">
          {error}
        </p>
      )}

      <div className="grid gap-6 sm:grid-cols-2">
        <section className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
          <h2 className="mb-3 font-semibold">Start a meeting</h2>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Meeting title"
            className="mb-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 outline-none focus:border-brand"
          />
          <button
            onClick={create}
            disabled={busy}
            className="w-full rounded-lg bg-brand px-3 py-2 font-medium text-white hover:bg-brand-dark disabled:opacity-50"
          >
            {busy ? "Creating…" : "Create & host"}
          </button>
        </section>

        <section className="rounded-xl border border-slate-700 bg-slate-800/60 p-5">
          <h2 className="mb-3 font-semibold">Join a meeting</h2>
          <input
            value={roomCode}
            onChange={(e) => setRoomCode(e.target.value.toUpperCase())}
            placeholder="Room code (e.g. X03RQ2)"
            className="mb-3 w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 uppercase outline-none focus:border-brand"
          />
          <button
            onClick={join}
            className="w-full rounded-lg bg-slate-700 px-3 py-2 font-medium text-white hover:bg-slate-600"
          >
            Join room
          </button>
        </section>
      </div>

      {recent.length > 0 && (
        <section className="mt-10">
          <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-500">
            Recent meetings
          </h2>
          <ul className="divide-y divide-slate-800 rounded-xl border border-slate-800">
            {recent.slice(0, 8).map((m) => (
              <li
                key={m.id}
                className="flex items-center justify-between px-4 py-3 text-sm"
              >
                <div>
                  <span className="font-medium">{m.title}</span>
                  <span className="ml-2 text-slate-500">{m.room_code}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`text-xs ${
                      m.is_active ? "text-emerald-400" : "text-slate-500"
                    }`}
                  >
                    {m.is_active ? "live" : "ended"}
                  </span>
                  {m.is_active ? (
                    <button
                      onClick={() => router.push(`/meeting/${m.room_code}`)}
                      className="text-brand hover:underline"
                    >
                      Join
                    </button>
                  ) : (
                    <button
                      onClick={() => router.push(`/summary/${m.id}`)}
                      className="text-slate-400 hover:underline"
                    >
                      Summary
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </section>
      )}
    </main>
  );
}
