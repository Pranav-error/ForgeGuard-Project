import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Analytics as AnalyticsData, type HistoryRow } from '../lib/api'
import { useAuth } from '../lib/auth'
import { LabelPill } from '../components/ui'

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function StatTile({ label, value, href }: { label: string; value: string | number; href?: string }) {
  const body = (
    <>
      <div className="text-[10.5px] font-bold text-slate-400 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-[26px] font-extrabold text-slate-800 leading-none">{value}</div>
    </>
  )
  const cls = 'bg-white border border-slate-200 rounded-xl px-5 py-4'
  return href ? (
    <Link to={href} className={`block ${cls} hover:border-brand-600 no-underline`}>
      {body}
    </Link>
  ) : (
    <div className={cls}>{body}</div>
  )
}

const STEPS = [
  {
    title: 'Register a reference signature',
    body: 'Optional, but lets the signature check compare a document against someone’s real signature instead of reporting it as missing evidence.',
    to: '/verify',
    cta: 'Register a signature',
  },
  {
    title: 'Verify your first document',
    body: 'Upload a scanned or photographed document and get a 0–100 score, a reason, and a tamper heatmap back in seconds.',
    to: '/verify',
    cta: 'Verify a document',
  },
  {
    title: 'Check Analytics and the audit trail',
    body: 'Every verification is scored, explained, and anchored to a tamper-evident ledger you can review later.',
    to: '/analytics',
    cta: 'Open Analytics',
  },
]

export function Dashboard() {
  const { session } = useAuth()
  const [stats, setStats] = useState<AnalyticsData | null>(null)
  const [recent, setRecent] = useState<HistoryRow[] | null>(null)

  useEffect(() => {
    if (!session) return
    api.analytics(session).then(setStats).catch(() => setStats(null))
    api.history(session).then((rows) => setRecent(rows.slice(0, 5))).catch(() => setRecent([]))
  }, [session])

  const isNew = stats !== null && stats.total === 0

  return (
    <div className="max-w-4xl mx-auto px-8 py-10">
      <div className="mb-8">
        <h1 className="font-display text-[28px] font-semibold tracking-tight mb-1.5">Welcome back</h1>
        <p className="text-[13.5px] text-slate-500">
          Signed in as {session?.email} · {session?.role}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <StatTile label="Total verifications" value={stats ? stats.total : '—'} />
        <StatTile label="Average score" value={stats?.avg_score ?? '—'} />
        <StatTile
          label="Most common result"
          value={stats && stats.total > 0 ? Object.entries(stats.by_label).sort((a, b) => b[1] - a[1])[0]?.[0] ?? '—' : '—'}
          href="/analytics"
        />
      </div>

      {isNew && (
        <div className="mb-8">
          <h2 className="text-[13px] font-bold text-slate-400 uppercase tracking-wide mb-3">Getting started</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {STEPS.map((s, i) => (
              <div key={s.title} className="bg-white border border-slate-200 rounded-xl p-5">
                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-brand-50 text-brand-600 text-[12px] font-bold mb-3">
                  {i + 1}
                </span>
                <h3 className="text-[13.5px] font-bold text-slate-800 mb-1.5">{s.title}</h3>
                <p className="text-[12px] text-slate-500 leading-relaxed mb-3.5">{s.body}</p>
                <Link to={s.to} className="text-[12.5px] font-semibold text-brand-600 hover:text-brand-700 no-underline">
                  {s.cta} →
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-[15px] font-bold m-0">Recent verifications</h2>
          {recent && recent.length > 0 && (
            <Link to="/history" className="text-[12.5px] font-semibold text-brand-600 hover:text-brand-700 no-underline">
              View all →
            </Link>
          )}
        </div>
        {recent === null && <p className="text-center py-10 text-slate-400 text-sm">Loading…</p>}
        {recent?.length === 0 && (
          <p className="text-center py-10 text-slate-400 text-[13.5px]">
            Nothing yet — <Link to="/verify" className="text-brand-600 font-semibold no-underline">verify your first document</Link> to see it here.
          </p>
        )}
        {recent && recent.length > 0 && (
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr>
                {['When', 'Type', 'Score', 'Label'].map((h) => (
                  <th key={h} className="text-left text-[11px] font-bold text-slate-400 uppercase tracking-wide pb-2.5 border-b border-slate-200">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {recent.map((r) => (
                <tr key={r.id}>
                  <td className="py-2.5 border-b border-slate-100">{formatDate(r.created_at)}</td>
                  <td className="py-2.5 border-b border-slate-100 capitalize">{r.doc_type}</td>
                  <td className="py-2.5 border-b border-slate-100 font-semibold">{r.final_score ?? '—'}</td>
                  <td className="py-2.5 border-b border-slate-100">
                    <LabelPill label={r.label} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
