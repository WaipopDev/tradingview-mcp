import Link from "next/link";

export default function SignalsPage() {
  return (
    <main className="min-h-screen px-6 py-8 sm:px-10 lg:px-16">
      <div className="mx-auto max-w-4xl rounded-3xl border border-white/10 bg-white/[0.04] p-8">
        <p className="text-sm uppercase tracking-[0.35em] text-sky-300/70">ขั้นต่อไป</p>
        <h1 className="mt-3 text-4xl font-bold">ประวัติสัญญาณ</h1>
        <p className="mt-4 text-slate-400">
          หน้านี้เตรียมไว้สำหรับ Phase ต่อไป: อ่านประวัติ `trade_signals` จาก SQLite/API แล้วแสดงตาราง ตัวกรอง และรีวิวผลย้อนหลัง
        </p>
        <Link className="mt-8 inline-flex rounded-full bg-sky-500 px-5 py-3 text-sm font-semibold text-slate-950" href="/">
          กลับไปสัญญาณล่าสุด
        </Link>
      </div>
    </main>
  );
}
