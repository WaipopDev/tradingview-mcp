import type { LatestSignal } from "@/lib/types";

function valueOrDash(value: unknown) {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "number") return Number.isInteger(value) ? value.toString() : value.toFixed(2);
  return String(value);
}

function biasClass(bias?: string) {
  if (bias === "BUY") return "border-emerald-400/40 bg-emerald-500/10 text-emerald-200";
  if (bias === "SELL") return "border-rose-400/40 bg-rose-500/10 text-rose-200";
  return "border-amber-400/40 bg-amber-500/10 text-amber-100";
}

function decisionThai(decision?: string) {
  if (decision === "TRADE") return "เข้าเงื่อนไขเทรด";
  if (decision === "WAIT_CONFIRMATION") return "รอยืนยัน";
  if (decision === "NO_TRADE") return "งดเทรด";
  return decision ?? "รอยืนยัน";
}

export function SignalCard({ signal }: { signal: LatestSignal }) {
  if (signal.error) {
    return (
      <section className="rounded-3xl border border-amber-400/30 bg-amber-500/10 p-6 text-amber-100">
        <p className="text-sm uppercase tracking-[0.3em] text-amber-200/70">ยังไม่มีสัญญาณใน cache</p>
        <h2 className="mt-3 text-2xl font-semibold">{signal.error.code}</h2>
        <p className="mt-2 text-sm text-amber-100/80">{signal.error.message ?? "รอ collector/score job เขียนข้อมูลลง DB ก่อน"}</p>
      </section>
    );
  }

  const support = Array.isArray((signal.levels as { support?: unknown[] } | undefined)?.support)
    ? ((signal.levels as { support?: number[] }).support?.join(" / ") ?? "-")
    : "-";
  const resistance = Array.isArray((signal.levels as { resistance?: unknown[] } | undefined)?.resistance)
    ? ((signal.levels as { resistance?: number[] }).resistance?.join(" / ") ?? "-")
    : "-";

  return (
    <section className="grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
      <div className={`rounded-3xl border p-6 shadow-2xl ${biasClass(signal.bias)}`}>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.3em] opacity-70">{signal.exchange ?? "OANDA"}:{signal.symbol ?? "XAUUSD"}</p>
            <h2 className="mt-3 text-5xl font-bold">{signal.bias ?? "WAIT"}</h2>
            <p className="mt-2 text-lg opacity-80">{decisionThai(signal.decision)}</p>
          </div>
          <div className="rounded-2xl bg-black/25 p-4 text-right">
            <p className="text-sm opacity-70">ราคา</p>
            <p className="text-3xl font-semibold">{valueOrDash(signal.price)}</p>
            <p className="mt-2 text-sm opacity-70">คะแนน {valueOrDash(signal.score)} / 100</p>
          </div>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-4">
          <Metric label="จุดเข้า" value={signal.plan?.entry_zone ?? "-"} />
          <Metric label="SL" value={valueOrDash(signal.plan?.sl)} />
          <Metric label="TP" value={signal.plan?.tp?.join(" / ") ?? "-"} />
          <Metric label="TF" value={signal.timeframe ?? "-"} />
        </div>
      </div>

      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6">
        <h3 className="text-xl font-semibold">บริบทตลาด</h3>
        <div className="mt-5 space-y-3 text-sm text-slate-300">
          <Row label="Regime" value={valueOrDash(signal.regime)} />
          <Row label="ความมั่นใจ" value={valueOrDash(signal.confidence)} />
          <Row label="อายุข้อมูล" value={`${signal.data_age_seconds ?? 0} วินาที`} />
          <Row label="แนวรับ" value={support} />
          <Row label="แนวต้าน" value={resistance} />
        </div>
      </div>
    </section>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl bg-black/20 p-4">
      <p className="text-xs uppercase tracking-[0.2em] opacity-60">{label}</p>
      <p className="mt-2 text-lg font-semibold">{value}</p>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-4 border-b border-white/10 pb-2">
      <span className="text-slate-500">{label}</span>
      <span className="text-right text-slate-100">{value}</span>
    </div>
  );
}
