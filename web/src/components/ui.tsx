import type { ReactNode } from 'react'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`bg-white border border-slate-200 rounded-2xl shadow-[0_1px_2px_rgba(16,24,40,.04)] p-6 mb-5 ${className}`}>{children}</section>
}

export function CardHead({ step, title, hint }: { step?: number | '✓'; title: string; hint?: string }) {
  return (
    <div className="flex items-center gap-3 mb-5">
      {step !== undefined && (
        <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full text-[13px] font-bold shrink-0 ${
          step === '✓' ? 'bg-emerald-50 text-emerald-700' : 'bg-brand-50 text-brand-600'
        }`}>
          {step}
        </span>
      )}
      <h2 className="text-[15px] font-bold m-0">{title}</h2>
      {hint && <span className="text-xs text-slate-400 ml-auto">{hint}</span>}
    </div>
  )
}

export function Field({ label, optional, children }: { label: string; optional?: boolean; children: ReactNode }) {
  return (
    <div className="mb-4">
      <label className="block text-xs font-semibold text-slate-600 mb-1.5">
        {label} {optional && <span className="font-normal text-slate-400">(optional)</span>}
      </label>
      {children}
    </div>
  )
}

export const inputClass =
  'w-full border border-slate-300 rounded-[10px] px-3.5 py-2.5 text-sm font-[inherit] text-slate-800 bg-white focus:outline-none focus:border-brand-600 focus:ring-[3px] focus:ring-brand-600/15'

export function PrimaryButton({
  children,
  loading,
  loadingText = 'Working…',
  className = '',
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean; loadingText?: string }) {
  return (
    <button
      {...rest}
      disabled={loading || rest.disabled}
      className={`inline-flex items-center gap-2 font-semibold text-[13.5px] rounded-[10px] px-[18px] py-2.5 text-white bg-brand-600 hover:bg-brand-700 disabled:bg-indigo-200 disabled:cursor-not-allowed ${className}`}
    >
      {loading && <span className="w-3.5 h-3.5 border-2 border-white/45 border-t-white rounded-full animate-spin" />}
      {loading ? loadingText : children}
    </button>
  )
}

export function GhostButton({
  children,
  loading,
  loadingText = 'Working…',
  className = '',
  ...rest
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { loading?: boolean; loadingText?: string }) {
  return (
    <button
      {...rest}
      disabled={loading || rest.disabled}
      className={`inline-flex items-center gap-2 font-semibold text-[13.5px] rounded-[10px] px-[18px] py-2.5 text-slate-700 bg-slate-100 hover:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed ${className}`}
    >
      {loading && <span className="w-3.5 h-3.5 border-2 border-slate-400/50 border-t-slate-600 rounded-full animate-spin" />}
      {loading ? loadingText : children}
    </button>
  )
}

export function FilePicker({ label, onChange, required }: { label: string; onChange: (f: File | null) => void; required?: boolean }) {
  return (
    <label className="flex items-center gap-2.5 border-[1.5px] border-dashed border-slate-300 rounded-[10px] px-3.5 py-2.5 text-[13px] text-slate-500 cursor-pointer hover:border-brand-600 hover:bg-indigo-50/40">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>
      <span>{label}</span>
      <input
        type="file"
        accept="image/*"
        required={required}
        className="hidden"
        onChange={(e) => onChange(e.target.files?.[0] ?? null)}
      />
    </label>
  )
}

export function Msg({ kind, children }: { kind: 'ok' | 'err'; children: ReactNode }) {
  return (
    <p
      className={`mt-3 text-[13px] px-3.5 py-2.5 rounded-[10px] ${
        kind === 'ok' ? 'text-emerald-700 bg-emerald-50 border border-emerald-200' : 'text-red-700 bg-red-50 border border-red-200'
      }`}
    >
      {children}
    </p>
  )
}

const LABEL_STYLES: Record<string, { bg: string; text: string }> = {
  Genuine: { bg: 'bg-emerald-100', text: 'text-emerald-700' },
  Suspicious: { bg: 'bg-amber-100', text: 'text-amber-700' },
  Forged: { bg: 'bg-red-100', text: 'text-red-700' },
  Failed: { bg: 'bg-slate-200', text: 'text-slate-600' },
}

export function LabelPill({ label }: { label: string }) {
  const s = LABEL_STYLES[label] ?? LABEL_STYLES.Failed
  return <span className={`px-3.5 py-1.5 rounded-full text-sm font-bold ${s.bg} ${s.text}`}>{label}</span>
}

export function scoreColor(label: string) {
  return (LABEL_STYLES[label] ?? LABEL_STYLES.Failed).text
}

export function SubScoreCard({ name, value }: { name: string; value: number | null }) {
  const missing = value === null || value === undefined
  const pct = missing ? 0 : Math.max(0, Math.min(100, value))
  const barColor = missing ? '#cbd5e1' : pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444'
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl p-3">
      <div className="text-[10.5px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">{name}</div>
      <div className={`text-lg font-extrabold mb-2 ${missing ? 'text-slate-300' : 'text-slate-800'}`}>{missing ? 'N/A' : pct}</div>
      <div className="bg-slate-200/70 rounded-full h-[7px] overflow-hidden">
        <div className="bar-fill h-full rounded-full" style={{ width: `${missing ? 0 : pct}%`, background: barColor }} />
      </div>
    </div>
  )
}
