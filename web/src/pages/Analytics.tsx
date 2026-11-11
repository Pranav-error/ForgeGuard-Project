import { useEffect, useState } from 'react'
import { api, type Analytics as AnalyticsData } from '../lib/api'
import { useAuth } from '../lib/auth'
import { Card, CardHead } from '../components/ui'

const LABEL_COLORS: Record<string, string> = {
  Genuine: '#10b981',
  Suspicious: '#f59e0b',
  Forged: '#ef4444',
  Failed: '#94a3b8',
}

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="bg-slate-50 border border-slate-200 rounded-xl px-4 py-3.5">
      <div className="text-[10.5px] font-bold text-slate-400 uppercase tracking-wide mb-1">{label}</div>
      <div className="text-2xl font-extrabold text-slate-800">{value}</div>
    </div>
  )
}

export function Analytics() {
  const { session } = useAuth()
  const [data, setData] = useState<AnalyticsData | null>(null)

  useEffect(() => {
    if (!session) return
    api.analytics(session).then(setData).catch(() => setData(null))
  }, [session])

  if (!data) {
    return (
      <div className="max-w-3xl mx-auto px-5 py-20 text-center text-slate-400 text-sm">Loading…</div>
    )
  }

  const labels = ['Genuine', 'Suspicious', 'Forged', 'Failed'] as const
  const maxLabelCount = Math.max(1, ...labels.map((l) => data.by_label[l] ?? 0))
  const maxDaily = Math.max(1, ...data.daily.map((d) => d.count))

  return (
    <div className="max-w-3xl mx-auto px-5">
      <div className="py-9">
        <h1 className="font-display text-[26px] font-semibold tracking-tight mb-1.5">Analytics</h1>
        <p className="text-[13.5px] text-slate-500">A summary of your verification activity.</p>
      </div>

      {data.total === 0 ? (
        <Card>
          <p className="text-center py-10 text-slate-400 text-[13.5px]">
            No verifications yet — results will show up here once you've run some on the Verify page.
          </p>
        </Card>
      ) : (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
            <StatTile label="Total verifications" value={data.total} />
            <StatTile label="Average score" value={data.avg_score ?? '—'} />
            <StatTile label="Avg. tamper sub-score" value={data.avg_sub_scores.tamper ?? 'N/A'} />
            <StatTile label="Avg. OCR sub-score" value={data.avg_sub_scores.ocr ?? 'N/A'} />
          </div>

          <Card>
            <CardHead title="Label breakdown" />
            <div className="space-y-3">
              {labels.map((l) => {
                const count = data.by_label[l] ?? 0
                const pct = (count / maxLabelCount) * 100
                return (
                  <div key={l} className="flex items-center gap-3">
                    <span className="w-20 text-xs font-semibold text-slate-600 shrink-0">{l}</span>
                    <div className="flex-1 bg-slate-100 rounded-full h-5 overflow-hidden">
                      <div
                        className="h-full rounded-full flex items-center justify-end pr-2 text-[10px] font-bold text-white transition-[width]"
                        style={{ width: `${Math.max(pct, count ? 8 : 0)}%`, background: LABEL_COLORS[l] }}
                      >
                        {count > 0 && count}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </Card>

          <Card>
            <CardHead title="Verifications over the last 14 days" />
            <div className="flex items-end gap-1.5 h-28">
              {data.daily.map((d) => (
                <div key={d.date} className="flex-1 flex flex-col items-center justify-end h-full gap-1" title={`${d.date}: ${d.count}`}>
                  <div
                    className="w-full rounded-t bg-brand-500"
                    style={{ height: `${Math.max((d.count / maxDaily) * 100, d.count ? 6 : 2)}%`, minHeight: 2 }}
                  />
                </div>
              ))}
            </div>
            <div className="flex justify-between mt-2 text-[10px] text-slate-400">
              <span>{data.daily[0]?.date.slice(5)}</span>
              <span>{data.daily[data.daily.length - 1]?.date.slice(5)}</span>
            </div>
          </Card>

          <Card>
            <CardHead title="Average sub-scores" />
            <div className="grid grid-cols-4 gap-3">
              {(['signature', 'tamper', 'ocr', 'anomaly'] as const).map((k) => (
                <div key={k} className="text-center">
                  <div className="text-xl font-extrabold text-slate-800">{data.avg_sub_scores[k] ?? 'N/A'}</div>
                  <div className="text-[11px] text-slate-400 uppercase tracking-wide mt-1">{k}</div>
                </div>
              ))}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}
