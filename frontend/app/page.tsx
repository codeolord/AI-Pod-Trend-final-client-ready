"use client";

import { useEffect, useMemo, useRef, useState } from "react";

type TrendItem = {
  id: number;
  title: string;
  url: string;
  source: string | null;
  source_url?: string | null;
  published_at: string | null;
  summary: string | null;
  ai_score_0_100: number | null;
  ai_niche: string | null;
  ai_status?: "pending" | "scored" | "failed" | string;
  ai_error?: string | null;
};

type Status = "idle" | "loading" | "error" | "success";
type IngestResponse = { task_id: string };

const BRAND_NAME = process.env.NEXT_PUBLIC_BRAND_NAME || "POD Trend Dashboard";
const BRAND_TAGLINE =
  process.env.NEXT_PUBLIC_BRAND_TAGLINE ||
  "AI-driven print-on-demand trend ingestion, scoring, and idea generation.";

function fmtDate(iso?: string | null) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleString();
  } catch {
    return iso;
  }
}

function apiBase() {
  return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
}

function wsUrl() {
  const base = apiBase();
  // convert http(s) -> ws(s)
  const wsBase = base.replace(/^http/i, "ws");
  return `${wsBase}/ws/trends`;
}

function getToken() {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("tv_access_token");
}

function setToken(t: string | null) {
  if (typeof window === "undefined") return;
  if (!t) window.localStorage.removeItem("tv_access_token");
  else window.localStorage.setItem("tv_access_token", t);
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken();
  const res = await fetch(`${apiBase()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    const msg = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}${msg ? ` - ${msg}` : ""}`);
  }
  return res.json();
}

export default function Page() {
  const [accessToken, setAccessToken] = useState<string | null>(null);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [items, setItems] = useState<TrendItem[]>([]);
  const [status, setStatus] = useState<Status>("idle");
  const [error, setError] = useState<string | null>(null);

  const [ingestStatus, setIngestStatus] = useState<Status>("idle");
  const [ingestMsg, setIngestMsg] = useState<string | null>(null);

  const [minScore, setMinScore] = useState<number>(0);
  const [query, setQuery] = useState<string>("");

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    setAccessToken(getToken());
  }, []);

  async function login() {
    setError(null);
    setStatus("loading");
    try {
      const out = await apiFetch<{ access_token: string }>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setToken(out.access_token);
      setAccessToken(out.access_token);
      setStatus("success");
    } catch (e: any) {
      setStatus("error");
      setError(e?.message || "Login failed");
    }
  }

  async function register() {
    setError(null);
    setStatus("loading");
    try {
      await apiFetch("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      await login();
    } catch (e: any) {
      setStatus("error");
      setError(e?.message || "Registration failed");
    }
  }

  function logout() {
    setToken(null);
    setAccessToken(null);
    setItems([]);
    setIngestMsg(null);
    setError(null);
    setStatus("idle");
    setIngestStatus("idle");
  }

  async function loadItems() {
    setError(null);
    setStatus("loading");
    try {
      const out = await apiFetch<TrendItem[]>("/api/v1/trends/items");
      setItems(out);
      setStatus("success");
    } catch (e: any) {
      setStatus("error");
      setError(e?.message || "Failed to load items");
    }
  }

  async function runIngest() {
    setIngestStatus("loading");
    setIngestMsg(null);
    try {
      const out = await apiFetch<IngestResponse>("/api/v1/trends/ingest", { method: "POST" });
      setIngestMsg(`Queued ingestion task: ${out.task_id}`);
      setIngestStatus("success");
    } catch (e: any) {
      setIngestStatus("error");
      setIngestMsg(e?.message || "Failed to start ingestion");
    }
  }

  // Connect WebSocket for realtime updates once authenticated.
  useEffect(() => {
    if (!accessToken) return;

    // initial load
    loadItems().catch(() => {});

    const url = wsUrl();
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data);
        if (msg?.type === "ingest_started") {
          setIngestMsg(`Ingestion started (${msg.feeds} feeds) …`);
          setIngestStatus("loading");
        } else if (msg?.type === "ingest_completed") {
          setIngestMsg(`Ingestion complete. created=${msg.created} updated=${msg.updated} scored=${msg.scored}`);
          setIngestStatus("success");
          // refresh list
          loadItems().catch(() => {});
        }
      } catch {
        // ignore
      }
    };

    ws.onerror = () => {
      // no-op; UI still works with manual refresh
    };

    return () => {
      try {
        ws.close();
      } catch {}
      wsRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [accessToken]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return items
      .filter((x) => (x.ai_score_0_100 ?? 0) >= minScore)
      .filter((x) => (!q ? true : (x.title || "").toLowerCase().includes(q) || (x.ai_niche || "").toLowerCase().includes(q)))
      .sort((a, b) => (b.ai_score_0_100 ?? -1) - (a.ai_score_0_100 ?? -1));
  }, [items, minScore, query]);

  if (!accessToken) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
        <h2 className="text-xl font-semibold">{BRAND_NAME}</h2>
        <p className="text-slate-300 mt-1 text-sm">{BRAND_TAGLINE}</p>

        <div className="mt-6 grid gap-3 max-w-md">
          <label className="text-sm text-slate-200">Email</label>
          <input
            className="rounded-xl bg-slate-950 border border-slate-800 px-3 py-2"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@company.com"
          />
          <label className="text-sm text-slate-200">Password</label>
          <input
            className="rounded-xl bg-slate-950 border border-slate-800 px-3 py-2"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            type="password"
            placeholder="min 8 characters"
          />

          {error ? <div className="text-sm text-red-300 mt-1">{error}</div> : null}

          <div className="flex gap-3 mt-2">
            <button
              onClick={login}
              className="rounded-xl bg-slate-50 text-slate-950 px-4 py-2 text-sm font-semibold"
              disabled={status === "loading"}
            >
              Log in
            </button>
            <button
              onClick={register}
              className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold"
              disabled={status === "loading"}
            >
              Create account
            </button>
          </div>

          <div className="text-xs text-slate-400 mt-2">
            Tip: For a client demo, create one admin user then log in from the dashboard.
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="grid gap-6">
      <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-3">
        <div>
          <h2 className="text-2xl font-semibold">{BRAND_NAME}</h2>
          <p className="text-slate-300 mt-1 text-sm">{BRAND_TAGLINE}</p>
        </div>

        <div className="flex gap-2">
          <button
            onClick={runIngest}
            className="rounded-xl bg-emerald-400 text-slate-950 px-4 py-2 text-sm font-semibold"
            disabled={ingestStatus === "loading"}
          >
            Run trend ingestion
          </button>
          <button
            onClick={loadItems}
            className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold"
            disabled={status === "loading"}
          >
            Refresh
          </button>
          <button onClick={logout} className="rounded-xl border border-slate-700 px-4 py-2 text-sm font-semibold">
            Logout
          </button>
        </div>
      </div>

      {ingestMsg ? (
        <div className="rounded-xl border border-slate-800 bg-slate-900/40 p-3 text-sm">
          {ingestStatus === "error" ? <span className="text-red-300">{ingestMsg}</span> : ingestMsg}
        </div>
      ) : null}

      <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-4">
        <div className="flex flex-col md:flex-row gap-3 md:items-center md:justify-between">
          <div className="flex gap-3 items-center">
            <div className="text-sm text-slate-300">Min score</div>
            <input
              type="range"
              min={0}
              max={100}
              value={minScore}
              onChange={(e) => setMinScore(Number(e.target.value))}
              className="w-48"
            />
            <div className="text-sm font-semibold">{minScore}</div>
          </div>
          <input
            className="w-full md:w-96 rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-sm"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search title or niche…"
          />
        </div>
      </div>

      {error ? <div className="text-sm text-red-300">{error}</div> : null}

      <div className="grid gap-3">
        {filtered.length === 0 ? (
          <div className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6 text-sm text-slate-300">
            No items yet. Click <span className="font-semibold text-slate-50">Run trend ingestion</span>.
          </div>
        ) : (
          filtered.map((item) => (
            <a
              key={item.id}
              href={item.url}
              target="_blank"
              className="block rounded-2xl border border-slate-800 bg-slate-900/40 p-5 hover:bg-slate-900/60 transition"
            >
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-2">
                <div className="min-w-0">
                  <div className="text-base font-semibold leading-snug break-words">{item.title}</div>
                  <div className="text-xs text-slate-400 mt-1">
                    {item.source ? item.source : "rss"} • {fmtDate(item.published_at)}
                  </div>
                  {item.summary ? <div className="text-sm text-slate-300 mt-2">{item.summary}</div> : null}
                </div>

                <div className="flex md:flex-col gap-2 md:items-end">
                  <div className="rounded-xl border border-slate-700 px-3 py-2 text-sm">
                    <div className="text-xs text-slate-400">AI score</div>
                    <div className="text-lg font-bold">{item.ai_score_0_100 ?? "—"}</div>
                  </div>
                  <div className="rounded-xl border border-slate-700 px-3 py-2 text-sm">
                    <div className="text-xs text-slate-400">Niche</div>
                    <div className="text-sm font-semibold">{item.ai_niche ?? "—"}</div>
                  </div>
                  <div className="text-xs text-slate-400">
                    {item.ai_status === "failed" ? (
                      <span className="text-red-300" title={item.ai_error || ""}>
                        AI failed
                      </span>
                    ) : item.ai_status === "pending" ? (
                      <span title="AI scoring is queued or disabled">AI pending</span>
                    ) : (
                      <span>AI scored</span>
                    )}
                  </div>
                </div>
              </div>
            </a>
          ))
        )}
      </div>

      <div className="text-xs text-slate-500">
        Realtime: ingestion status updates are pushed over WebSocket. If your network blocks WS, the dashboard still works with the Refresh button.
      </div>
    </div>
  );
}
