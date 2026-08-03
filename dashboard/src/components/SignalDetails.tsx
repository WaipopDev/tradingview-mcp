import type { LatestSignal } from "@/lib/types";

const KEY_LABELS: Record<string, string> = {
  anchor_price: "ราคาอ้างอิง",
  expected_move_points: "ระยะคาดหวัง",
  expected_move_source: "แหล่งที่มา",
  timeframe: "ไทม์เฟรม",
  sd1_low: "SD1 ล่าง",
  sd1_high: "SD1 บน",
  sd2_low: "SD2 ล่าง",
  sd2_high: "SD2 บน",
  range_state: "สถานะกรอบ",
  real_open_interest_available: "มี OI จริง",
  source: "แหล่งข้อมูล",
  limitation: "ข้อจำกัด",
  magnet_zone: "โซนแม่เหล็ก",
  support_levels: "แนวรับ",
  resistance_levels: "แนวต้าน",
  flow_direction: "ทิศทาง Flow",
  flow_confidence: "ความมั่นใจ Flow",
  regime_hint: "Regime hint",
  notes: "บันทึก",
  state: "สถานะ",
  ratio: "อัตราส่วน",
  atr_volatility: "ความผันผวน ATR",
};

export function SignalDetails({ signal }: { signal: LatestSignal }) {
  const reasonCodes = signal.reason_codes ?? [];
  return (
    <section className="grid gap-4 lg:grid-cols-3">
      <Panel title="กรอบ SD" data={signal.sd_range} />
      <Panel title="OI / Flow Proxy" data={signal.oi_proxy} />
      <Panel title="ปริมาณ / ATR" data={signal.volume} />
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:col-span-3">
        <h3 className="text-xl font-semibold">เงื่อนไขถาม AI</h3>
        <div className="mt-4 grid gap-3 text-sm md:grid-cols-4">
          <GateItem label="ถาม AI" value={signal.ai_gate?.should_ask_ai ? "ใช่" : "ไม่"} />
          <GateItem label="เหตุผล" value={translateGateReason(signal.ai_gate?.reason)} />
          <GateItem label="Fingerprint" value={signal.ai_gate?.signal_fingerprint ?? "-"} />
          <GateItem label="Cache" value={signal.ai_gate?.cached_response ? "ใช้คำตอบเดิมได้" : "-"} />
        </div>
      </div>
      <div className="rounded-3xl border border-white/10 bg-white/[0.04] p-6 lg:col-span-3">
        <h3 className="text-xl font-semibold">เหตุผลของระบบ</h3>
        {reasonCodes.length > 0 ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {reasonCodes.map((code) => (
              <span key={code} className="rounded-full border border-sky-400/30 bg-sky-500/10 px-3 py-1 text-sm text-sky-100">
                {translateReasonCode(code)}
              </span>
            ))}
          </div>
        ) : (
          <p className="mt-4 text-sm text-slate-500">ยังไม่มีเหตุผลจากระบบ</p>
        )}
      </div>
    </section>
  );
}

function translateGateReason(reason?: string) {
  if (reason === "TRADE_SIGNAL_NEEDS_AI_SUMMARY") return "เข้าเงื่อนไขเทรด ต้องให้ AI สรุป";
  if (reason === "CACHED_AI_RESPONSE_REUSABLE") return "ใช้คำตอบ AI เดิมได้";
  if (reason === "NO_TRADE_CONDITION") return "ยังไม่เข้าเงื่อนไขเทรด";
  return reason ?? "-";
}

function translateReasonCode(code: string) {
  const mapping: Record<string, string> = {
    STORED_FROM_AUTOMATION_CONNECTOR: "บันทึกจากระบบอัตโนมัติ",
    SD_OI_PROXY_ATTACHED: "แนบ SD/OI proxy แล้ว",
    DECISION_TRADE: "เข้าเงื่อนไขเทรด",
    DECISION_WAIT_CONFIRMATION: "รอยืนยัน",
    DECISION_NO_TRADE: "งดเทรด",
    REGIME_range_mean_reversion: "Regime: Range / Mean Reversion",
    REGIME_trend_momentum: "Regime: Trend / Momentum",
    REGIME_low_vol_squeeze: "Regime: Low-vol Squeeze",
    REGIME_event_guard: "Regime: Event Guard",
  };
  return mapping[code] ?? code;
}

function labelFor(key: string) {
  return KEY_LABELS[key] ?? key;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "ใช่" : "ไม่";
  if (typeof value === "number") return Number.isInteger(value) ? value.toString() : value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  if (Array.isArray(value)) return value.length ? value.map(formatValue).join(" / ") : "-";
  return String(value);
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
              <span className="text-slate-500">{labelFor(key)}</span>
              <span className="max-w-[60%] text-right text-slate-100">{formatValue(value)}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-500">ยังไม่มีข้อมูล</p>
      )}
    </div>
  );
}
