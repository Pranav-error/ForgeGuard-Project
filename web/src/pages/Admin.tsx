import { useEffect, useState } from 'react'
import { api, type AuditLogRow } from '../lib/api'
import { useAuth } from '../lib/auth'
import { Card, CardHead, GhostButton } from '../components/ui'

function formatDate(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export function Admin() {
  const { session } = useAuth()
  const [logs, setLogs] = useState<AuditLogRow[] | null>(null)
  const [ledger, setLedger] = useState<{ valid: boolean; length: number; broken_at: number | null } | null>(null)
  const [checking, setChecking] = useState(false)

  useEffect(() => {
    if (!session) return
    api.auditLog(session).then(setLogs).catch(() => setLogs([]))
  }, [session])

  async function checkLedger() {
    if (!session) return
    setChecking(true)
    try {
      setLedger(await api.verifyLedger(session))
    } finally {
      setChecking(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto px-5">
      <div className="py-9">
        <h1 className="font-display text-[26px] font-semibold tracking-tight mb-1.5">Admin</h1>
        <p className="text-[13.5px] text-slate-500">Audit trail and ledger integrity.</p>
      </div>

      <Card>
        <CardHead title="Ledger integrity (Phase 2)" />
        <p className="text-[13px] text-slate-500 mb-4">
          Re-derives every block's hash and checks the chain is unbroken — detects any row edited
          directly in the database, bypassing the API entirely.
        </p>
        <GhostButton onClick={checkLedger} loading={checking} loadingText="Checking…">
          Run integrity check
        </GhostButton>
        {ledger && (
          <div
            className={`mt-4 text-[13px] px-4 py-3 rounded-[10px] border ${
              ledger.valid ? 'bg-emerald-50 border-emerald-200 text-emerald-700' : 'bg-red-50 border-red-200 text-red-700'
            }`}
          >
            {ledger.valid
              ? `Chain intact — ${ledger.length} block(s), all hashes verified.`
              : `Chain broken at block ${ledger.broken_at} (of ${ledger.length}).`}
          </div>
        )}
      </Card>

      <Card>
        <CardHead title="Audit log" />
        {logs === null && <p className="text-center py-8 text-slate-400 text-sm">Loading…</p>}
        {logs?.length === 0 && <p className="text-center py-8 text-slate-400 text-[13.5px]">Nothing logged yet.</p>}
        {logs && logs.length > 0 && (
          <table className="w-full border-collapse text-[12.5px]">
            <thead>
              <tr>
                {['When', 'Action', 'Detail'].map((h) => (
                  <th key={h} className="text-left text-[11px] font-bold text-slate-400 uppercase tracking-wide pb-2.5 border-b border-slate-200">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id}>
                  <td className="py-2.5 border-b border-slate-100 whitespace-nowrap">{formatDate(l.created_at)}</td>
                  <td className="py-2.5 border-b border-slate-100 font-semibold">{l.action}</td>
                  <td className="py-2.5 border-b border-slate-100 text-slate-500 font-mono text-[11px]">{l.detail_json}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  )
}
