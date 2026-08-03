import type { LatestSignal } from "@/lib/types";

export function SignalDetails({ signal }: { signal: LatestSignal }) {
  const reasonCodes = signal.reason_codes ?? [];
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <Panel title="SD Range" data={signal.sd_range} />
      <Panel title="OI / Flow Proxy" data={signal.oi_proxy} />
      <Panel title="Volume" data={signal.volume} />
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:col-span-3">
        <h3 className="text-xl font-semibold">AI Gate</h3>
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
          <GateItem label="Ask AI" value={signal.ai_gate?.should_ask_ai ? "YES" : "NO"} />
          <GateItem label="Reason" value={signal.ai_gate?.reason ?? "-"} />
          <GateItem label="Fingerprint" value={signal.ai_gate?.signal_fingerprint ?? "-"} />
          <GateItem label="Cache" value={signal.ai_gate?.cached_response ? "REUSABLE" : "-"} />
        </div>
      </div>
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:col-span-3">
        <h3 className="text-xl font-semibold">Reason Codes</h3>
        {reasonCodes.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {reasonCodes.map((code) => (
              <span key={code} className="rounded-full border border-sky-400/30 bg-sky-500/10 px-3 py-1 text-sm text-sky-100">
                {code}
              </span>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">ยังไม่มี reason code</p>
        )}
      </div>
    </section>
  );
}

function GateItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-white/10 bg-black/20 p-3">
      <p className="text-xs uppercase tracking-[0.2em] text-slate-500">{label}</p>
      <p className="mt-2 break-all text-slate-100">{value}</p>
    </div>
  );
}

function Panel({ title, data }: { title: string; data?: Record<string, unknown> }) {
  const entries = Object.entries(data ?? {});
  return (
    <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
      <h3 className="text-xl font-semibold">{title}</h3>
      {entries.length > 0 ? (
        <div className="mt-4 space-y-2 text-sm">
          {entries.map(([key, value]) => (
            <div key={key} className="flex justify-between gap-4 border-b border-white/10 pb-2">
              <span className="text-slate-500">{key}</span>
              <span className="text-right text-slate-100">{Array.isArray(value) ? value.join(" / ") : String(value)}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">ยังไม่มีข้อมูล</p>
      )}
    </div>
  );
}
