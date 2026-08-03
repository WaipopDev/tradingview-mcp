"use client";

import { useCallback, useEffect, useState } from "react";
import { SignalCard } from "@/components/SignalCard";
import { SignalDetails } from "@/components/SignalDetails";
import type { LatestSignal } from "@/lib/types";

export default function Home() {
  const [signal, setSignal] = useState<LatestSignal | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatedAt, setUpdatedAt] = useState<string>("");

  const loadSignal = useCallback(async () => {
    setLoading(true);
    const response = await fetch("/api/signals/latest?symbol=XAUUSD&timeframe=15m", { cache: "no-store" });
    const payload = (await response.json()) as LatestSignal;
    setSignal(payload);
    setUpdatedAt(new Date().toLocaleTimeString());
    setLoading(false);
  }, []);

  useEffect(() => {
    const initialTimer = window.setTimeout(() => void loadSignal(), 0);
    const timer = window.setInterval(() => void loadSignal(), 30_000);
    return () => {
      window.clearTimeout(initialTimer);
      window.clearInterval(timer);
    };
  }, [loadSignal]);

  return (
    <main className="min-h-screen px-6 py-8 sm:px-10 lg:px-16">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.35em] text-sky-300/70">TradingView MCP</p>
            <h1 className="mt-3 text-4xl font-bold sm:text-5xl">Trad Dashboard</h1>
            <p className="mt-3 max-w-2xl text-slate-400">
              Dashboard อ่าน compact signal จาก Python SQLite cache เพื่อลด token ก่อนส่งให้ AI สรุปแผน BUY/SELL
            </p>
          </div>
          <button
            onClick={() => void loadSignal()}
            className="rounded-full border border-sky-400/40 bg-sky-500/10 px-5 py-3 text-sm font-semibold text-sky-100 transition hover:bg-sky-500/20"
          >
            {loading ? "Loading..." : "Refresh"}
          </button>
        </header>

        {signal ? <SignalCard signal={signal} /> : <div className="rounded-3xl border border-white/10 p-8 text-slate-400">Loading signal...</div>}
        {signal ? <SignalDetails signal={signal} /> : null}

        <footer className="text-sm text-slate-500">
          Updated: {updatedAt || "-"} · API: /api/signals/latest · DB: TRADINGVIEW_MCP_DB_PATH หรือ ~/.tradingview-mcp/trading_signals.sqlite3
        </footer>
      </div>
    </main>
  );
}
