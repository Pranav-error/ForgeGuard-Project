import { Fragment, useEffect, useState } from 'react'
import { api, type HistoryRow } from '../lib/api'
import { useAuth } from '../lib/auth'
import { LabelPill } from '../components/ui'

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function History() {
  const { session } = useAuth()
  const [rows, setRows] = useState<HistoryRow[] | null>(null)
  const [expanded, setExpanded] = useState<string | null>(null)

  useEffect(() => {
    if (!session) return
    api.history(session).then(setRows).catch(() => setRows([]))
  }, [session])

  return (
    <div className="max-w-3xl mx-auto px-5">
      <div className="py-9">
        <h1 className="text-[22px] font-extrabold tracking-tight mb-1.5">History</h1>
        <p className="text-[13.5px] text-slate-500">Every document you've verified.</p>
      </div>

      <section className="bg-white border border-slate-200 rounded-2xl p-6">
        {rows === null && <p className="text-center py-12 text-slate-400 text-sm">Loading…</p>}
        {rows?.length === 0 && <p className="text-center py-12 text-slate-400 text-[13.5px]">No verifications yet — try the Verify page.</p>}
        {rows && rows.length > 0 && (
          <table className="w-full border-collapse text-[13px]">
            <thead>
              <tr>
                {['When', 'Type', 'Score', 'Label', ''].map((h) => (
                  <th key={h} className="text-left text-[11px] font-bold text-slate-400 uppercase tracking-wide pb-2.5 border-b border-slate-200">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <Fragment key={r.id}>
                  <tr
                    className="cursor-pointer hover:bg-slate-50"
                    onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                  >
                    <td className="py-2.5 border-b border-slate-100">{formatDate(r.created_at)}</td>
                    <td className="py-2.5 border-b border-slate-100 capitalize">{r.doc_type}</td>
                    <td className="py-2.5 border-b border-slate-100 font-semibold">{r.final_score ?? '—'}</td>
                    <td className="py-2.5 border-b border-slate-100">
                      <LabelPill label={r.label} />
                    </td>
                    <td className="py-2.5 border-b border-slate-100 text-slate-400">{expanded === r.id ? '▲' : '▼'}</td>
                  </tr>
                  {expanded === r.id && (
                    <tr>
                      <td colSpan={5} className="pb-4 border-b border-slate-100">
                        <div className="bg-slate-50 border border-slate-200 rounded-[10px] px-4 py-3 text-[13px] text-slate-600 mb-2">
                          {r.reason_text}
                        </div>
                        <div className="grid grid-cols-4 gap-2 text-[12px] text-slate-500">
                          <div>Signature: {r.signature_sub_score ?? 'N/A'}</div>
                          <div>Tamper: {r.tamper_sub_score ?? 'N/A'}</div>
                          <div>OCR: {r.ocr_sub_score ?? 'N/A'}</div>
                          <div>Anomaly: {r.anomaly_sub_score ?? 'N/A'}</div>
                        </div>
                      </td>
                    </tr>
                  )}
                </Fragment>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  )
}
