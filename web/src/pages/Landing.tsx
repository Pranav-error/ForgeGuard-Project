import { Link } from 'react-router-dom'

const FEATURES = [
  {
    title: 'Tamper Localisation',
    body: 'A dual-stream (SRM noise-residual + semantic RGB) network pinpoints edited pixels and renders a heatmap over the suspicious regions.',
  },
  {
    title: 'Signature Verification',
    body: 'Detects, cleans and compares a signature against stored references with a writer-independent metric-learning model — no retraining for a new signer.',
  },
  {
    title: 'OCR & Field Validation',
    body: 'Extracts text, checks field formats, and for financial documents verifies the arithmetic actually adds up.',
  },
  {
    title: 'Anomaly Detection',
    body: 'An autoencoder trained only on genuine pages flags forgery types none of the other models were ever trained to recognise.',
  },
]

export function Landing() {
  return (
    <div className="max-w-4xl mx-auto px-5">
      <div className="flex items-center justify-between py-8">
        <div className="flex items-center gap-2.5 font-extrabold text-[15px] text-slate-900">
          <span className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </span>
          ForgeGuard
        </div>
        <Link to="/login" className="text-[13.5px] font-semibold text-slate-600 hover:text-slate-900 no-underline">
          Sign in
        </Link>
      </div>

      <div className="py-16 text-center">
        <span className="inline-block text-[11.5px] font-bold uppercase tracking-wide text-brand-600 bg-brand-50 px-3 py-1 rounded-full mb-5">
          College major project · REVA University
        </span>
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 mb-5 leading-[1.1]">
          Is this document real?
        </h1>
        <p className="text-base text-slate-500 max-w-xl mx-auto mb-8">
          ForgeGuard combines tamper localisation, signature verification, OCR validation and
          anomaly detection into one explainable score — never a bare "forged" label, always a
          reason, a heatmap, and a tamper-evident audit trail.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 font-semibold text-sm rounded-[10px] px-6 py-3 text-white bg-brand-600 hover:bg-brand-700 no-underline"
        >
          Get started →
        </Link>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pb-20">
        {FEATURES.map((f) => (
          <div key={f.title} className="bg-white border border-slate-200 rounded-2xl p-5">
            <h3 className="text-sm font-bold text-slate-800 mb-1.5">{f.title}</h3>
            <p className="text-[13px] text-slate-500 leading-relaxed">{f.body}</p>
          </div>
        ))}
      </div>

      <p className="text-center text-xs text-slate-400 pb-10">
        <a href="https://github.com/Pranav-error/ForgeGuard-Project" className="text-slate-400 hover:text-slate-600">
          View source on GitHub
        </a>
      </p>
    </div>
  )
}
