import { Link } from 'react-router-dom'
import { Logo } from '../components/ui'

const FEATURES = [
  {
    title: 'Tamper Localisation',
    body: 'A dual-stream (SRM noise-residual + semantic RGB) network pinpoints edited pixels and renders a heatmap over the suspicious regions.',
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" /><path d="m9 12 2 2 4-4" /></svg>
    ),
  },
  {
    title: 'Signature Verification',
    body: 'Detects, cleans and compares a signature against stored references with a writer-independent metric-learning model — no retraining for a new signer.',
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 17c2-3 4-3 6 0s4 3 6 0 4-3 6 0" /><path d="M3 20h18" /></svg>
    ),
  },
  {
    title: 'OCR & Field Validation',
    body: 'Extracts text, checks field formats, and for financial documents verifies the arithmetic actually adds up.',
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="4" y="3" width="16" height="18" rx="1.5" /><path d="M8 8h8M8 12h8M8 16h5" /></svg>
    ),
  },
  {
    title: 'Anomaly Detection',
    body: 'An autoencoder trained only on genuine pages flags forgery types none of the other models were ever trained to recognise.',
    icon: (
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path d="M9.5 9.5h.01M14.5 9.5h.01" /><path d="M8 15c1.5-1.5 6.5-1.5 8 0" /></svg>
    ),
  },
]

function MockResultPanel() {
  const subs = [
    { name: 'Signature', value: 49, color: '#b6872f' },
    { name: 'Tamper', value: 32, color: '#dc2626' },
    { name: 'OCR', value: 100, color: '#10b981' },
    { name: 'Anomaly', value: 61, color: '#b6872f' },
  ]
  return (
    <div className="min-w-0 bg-white border border-slate-200 rounded-xl shadow-[0_8px_28px_rgba(15,23,42,.08)] p-5 sm:p-6 lg:rotate-[0.6deg]">
      <div className="flex items-center justify-between mb-4">
        <span className="text-[10.5px] font-bold uppercase tracking-wide text-slate-400">Verification result</span>
        <span className="text-[10.5px] font-mono text-slate-300">doc_a7f2…</span>
      </div>
      <div className="flex items-baseline gap-3 mb-4">
        <span className="px-3 py-1 rounded-full text-[13px] font-bold bg-amber-100 text-amber-700">Suspicious</span>
        <span className="text-[30px] font-display font-semibold tracking-tight text-slate-900">42</span>
        <span className="text-slate-400 text-[12.5px]">/ 100</span>
      </div>
      <p className="text-[12.5px] text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-3.5 py-2.5 mb-4.5">
        lowest-confidence check: tamper (32/100) — edited region detected near the date field
      </p>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 mb-5">
        {subs.map((s) => (
          <div key={s.name} className="min-w-0 bg-slate-50 border border-slate-200 rounded-lg p-2.5">
            <div className="text-[9px] font-bold text-slate-400 uppercase tracking-wide mb-1 truncate">{s.name}</div>
            <div className="text-[15px] font-extrabold text-slate-800 mb-1.5">{s.value}</div>
            <div className="bg-slate-200/70 rounded-full h-[5px] overflow-hidden">
              <div className="h-full rounded-full" style={{ width: `${s.value}%`, background: s.color }} />
            </div>
          </div>
        ))}
      </div>
      <div className="relative bg-slate-100 border border-slate-200 rounded-lg h-24 overflow-hidden">
        <div className="absolute inset-0" style={{ backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 7px, rgba(15,23,42,.04) 7px, rgba(15,23,42,.04) 8px)' }} />
        <div className="absolute left-[38%] top-[30%] w-14 h-8 rounded border-2 border-red-500/70 bg-red-500/10" />
        <span className="absolute left-[38%] top-[18%] text-[10px] font-bold text-red-600">1</span>
        <span className="absolute left-3 bottom-2 text-[9.5px] font-semibold text-slate-400 uppercase tracking-wide">Tamper heatmap</span>
      </div>
    </div>
  )
}

export function Landing() {
  return (
    <div className="max-w-6xl mx-auto px-5">
      <div className="flex items-center justify-between py-7">
        <Logo />
        <Link to="/login" className="text-[13.5px] font-semibold text-slate-600 hover:text-slate-900 no-underline">
          Sign in
        </Link>
      </div>

      <div className="grid lg:grid-cols-[1.05fr_1fr] gap-10 lg:gap-14 items-center py-12 lg:py-16">
        <div className="min-w-0">
          <span className="inline-block text-[11px] font-bold uppercase tracking-wide text-gold-600 bg-gold-100 px-3 py-1 rounded-full mb-6">
            College major project · REVA University
          </span>
          <h1 className="font-display text-[36px] sm:text-[54px] font-semibold tracking-tight text-slate-900 mb-5 leading-[1.08]">
            Is this document real?
          </h1>
          <p className="text-[15.5px] text-slate-500 max-w-md mb-8 leading-relaxed">
            ForgeGuard combines tamper localisation, signature verification, OCR validation and
            anomaly detection into one explainable score — never a bare "forged" label, always a
            reason, a heatmap, and a tamper-evident audit trail.
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 font-semibold text-sm rounded-lg px-6 py-3 text-white bg-brand-600 hover:bg-brand-700 no-underline"
          >
            Get started →
          </Link>
          <div className="flex flex-wrap gap-x-6 gap-y-2 mt-9 font-mono text-[11.5px] text-slate-400">
            <span>4 independent checks</span>
            <span className="text-slate-300">·</span>
            <span>hash-chain ledger</span>
            <span className="text-slate-300">·</span>
            <span>0–100 explainable score</span>
          </div>
        </div>
        <MockResultPanel />
      </div>

      <div className="border-t border-slate-200 py-14">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-10 gap-y-9">
          {FEATURES.map((f) => (
            <div key={f.title} className="flex gap-3.5">
              <div className="w-9 h-9 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center shrink-0">{f.icon}</div>
              <div>
                <h3 className="text-[14px] font-bold text-slate-800 mb-1">{f.title}</h3>
                <p className="text-[13px] text-slate-500 leading-relaxed">{f.body}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <p className="text-center text-xs text-slate-400 pb-10">
        <a href="https://github.com/Pranav-error/ForgeGuard-Project" className="text-slate-400 hover:text-slate-600">
          View source on GitHub
        </a>
      </p>
    </div>
  )
}
