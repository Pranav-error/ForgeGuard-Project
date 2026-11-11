import { useState } from 'react'
import { api, ApiError, type BatchResultRow, type VerificationResult } from '../lib/api'
import { useAuth } from '../lib/auth'
import {
  Card,
  CardHead,
  Field,
  FilePicker,
  GhostButton,
  LabelPill,
  Msg,
  PrimaryButton,
  SubScoreCard,
  inputClass,
  scoreColor,
} from '../components/ui'

const DOC_TYPES = [
  { value: 'identity', label: 'Identity card' },
  { value: 'certificate', label: 'Certificate' },
  { value: 'invoice', label: 'Invoice' },
  { value: 'legal', label: 'Legal document' },
]

export function Verify() {
  const { session } = useAuth()

  const [signerId, setSignerId] = useState('')
  const [sigFile, setSigFile] = useState<File | null>(null)
  const [sigLoading, setSigLoading] = useState(false)
  const [sigMsg, setSigMsg] = useState<{ kind: 'ok' | 'err'; text: string } | null>(null)

  const [docType, setDocType] = useState('identity')
  const [verifySignerId, setVerifySignerId] = useState('')
  const [docFile, setDocFile] = useState<File | null>(null)
  const [verifyLoading, setVerifyLoading] = useState(false)
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [heatmapSrc, setHeatmapSrc] = useState<string | null>(null)
  const [verifyError, setVerifyError] = useState<string | null>(null)
  const [reportLoading, setReportLoading] = useState(false)

  const [batchFiles, setBatchFiles] = useState<File[]>([])
  const [batchDocType, setBatchDocType] = useState('identity')
  const [batchLoading, setBatchLoading] = useState(false)
  const [batchResults, setBatchResults] = useState<BatchResultRow[] | null>(null)

  async function handleRegisterSignature(e: React.FormEvent) {
    e.preventDefault()
    if (!session || !sigFile) return
    setSigLoading(true)
    setSigMsg(null)
    try {
      const data = await api.registerSignature(session, signerId, sigFile)
      setSigMsg({ kind: 'ok', text: `Reference signature registered for "${data.signer_id}".` })
    } catch (err) {
      setSigMsg({ kind: 'err', text: err instanceof ApiError ? err.message : 'Failed to register signature' })
    } finally {
      setSigLoading(false)
    }
  }

  async function handleVerify(e: React.FormEvent) {
    e.preventDefault()
    if (!session || !docFile) return
    setVerifyLoading(true)
    setVerifyError(null)
    try {
      const data = await api.verifyDocument(session, docFile, docType, verifySignerId)
      setResult(data)
      setHeatmapSrc(data.heatmap_url ? await api.fetchHeatmap(session, data.heatmap_url) : null)
    } catch (err) {
      setVerifyError(err instanceof ApiError ? err.message : 'Verification failed')
    } finally {
      setVerifyLoading(false)
    }
  }

  async function handleDownloadReport() {
    if (!session || !result) return
    setReportLoading(true)
    try {
      await api.downloadReport(session, result.document_id)
    } catch {
      // non-critical; the result panel itself already succeeded
    } finally {
      setReportLoading(false)
    }
  }

  async function handleBatchVerify(e: React.FormEvent) {
    e.preventDefault()
    if (!session || batchFiles.length === 0) return
    setBatchLoading(true)
    setBatchResults(null)
    try {
      setBatchResults(await api.verifyBatch(session, batchFiles, batchDocType, ''))
    } finally {
      setBatchLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto px-8 py-10">
      <div className="mb-8">
        <h1 className="font-display text-[28px] font-semibold tracking-tight mb-1.5">Verify a document</h1>
        <p className="text-[13.5px] text-slate-500">Register a reference signature, then upload a document to run the full pipeline.</p>
      </div>

      <div className="grid lg:grid-cols-[1fr_380px] gap-6 items-start">
        <div className="min-w-0">
          <Card>
            <CardHead step={1} title="Register a reference signature" hint="optional" />
            <form onSubmit={handleRegisterSignature}>
              <Field label="Signer ID">
                <input required className={inputClass} placeholder="e.g. jane_doe" value={signerId} onChange={(e) => setSignerId(e.target.value)} />
              </Field>
              <Field label="Signature crop image">
                <FilePicker label={sigFile?.name ?? 'Choose an image…'} onChange={setSigFile} required />
              </Field>
              <GhostButton type="submit" loading={sigLoading} loadingText="Registering…" disabled={!sigFile}>
                Register signature
              </GhostButton>
            </form>
            {sigMsg && <Msg kind={sigMsg.kind}>{sigMsg.text}</Msg>}
          </Card>

          <Card>
            <CardHead step={2} title="Upload a document" />
            <form onSubmit={handleVerify}>
              <div className="flex gap-3.5 max-sm:flex-col">
                <div className="flex-1 min-w-0">
                  <Field label="Document type">
                    <select className={inputClass} value={docType} onChange={(e) => setDocType(e.target.value)}>
                      {DOC_TYPES.map((d) => (
                        <option key={d.value} value={d.value}>
                          {d.label}
                        </option>
                      ))}
                    </select>
                  </Field>
                </div>
                <div className="flex-1 min-w-0">
                  <Field label="Signer ID" optional>
                    <input className={inputClass} placeholder="e.g. jane_doe" value={verifySignerId} onChange={(e) => setVerifySignerId(e.target.value)} />
                  </Field>
                </div>
              </div>
              <Field label="Document image">
                <FilePicker label={docFile?.name ?? 'Choose an image…'} onChange={setDocFile} required />
              </Field>
              <PrimaryButton type="submit" loading={verifyLoading} loadingText="Verifying…" disabled={!docFile}>
                Verify document
              </PrimaryButton>
            </form>
            {verifyError && <Msg kind="err">{verifyError}</Msg>}
          </Card>

          <Card className="mb-0">
            <CardHead step={3} title="Batch verify multiple documents" hint="optional" />
            <form onSubmit={handleBatchVerify}>
              <Field label="Document type">
                <select className={inputClass} value={batchDocType} onChange={(e) => setBatchDocType(e.target.value)}>
                  {DOC_TYPES.map((d) => (
                    <option key={d.value} value={d.value}>
                      {d.label}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Document images">
                <FilePicker
                  label={batchFiles.length > 0 ? `${batchFiles.length} file(s) selected` : 'Choose multiple images…'}
                  multiple
                  onMultiChange={setBatchFiles}
                />
              </Field>
              <PrimaryButton type="submit" loading={batchLoading} loadingText={`Verifying ${batchFiles.length}…`} disabled={batchFiles.length === 0}>
                Verify batch
              </PrimaryButton>
            </form>

            {batchResults && (
              <table className="w-full border-collapse text-[13px] mt-5">
                <thead>
                  <tr>
                    {['File', 'Score', 'Label', 'Reason'].map((h) => (
                      <th key={h} className="text-left text-[11px] font-bold text-slate-400 uppercase tracking-wide pb-2.5 border-b border-slate-200">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {batchResults.map((r, i) => (
                    <tr key={i}>
                      <td className="py-2.5 border-b border-slate-100">{r.filename}</td>
                      {r.error ? (
                        <td colSpan={3} className="py-2.5 border-b border-slate-100 text-red-600">
                          {r.error}
                        </td>
                      ) : (
                        <>
                          <td className="py-2.5 border-b border-slate-100 font-semibold">{r.score ?? '—'}</td>
                          <td className="py-2.5 border-b border-slate-100">{r.label && <LabelPill label={r.label} />}</td>
                          <td className="py-2.5 border-b border-slate-100 text-slate-500 text-[12px]">{r.reason}</td>
                        </>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </Card>
        </div>

        <div className="lg:sticky lg:top-8">
          {result ? (
            <Card className="mb-0">
              <div className="flex items-start justify-between mb-4.5">
                <CardHead title="Result" />
                <GhostButton className="!px-3.5 !py-2 !text-xs" onClick={handleDownloadReport} loading={reportLoading} loadingText="Generating…">
                  Download report
                </GhostButton>
              </div>
              <div className="flex items-baseline gap-3 mb-4.5">
                <LabelPill label={result.label} />
                <span className={`text-[32px] font-extrabold tracking-tight ${scoreColor(result.label)}`}>{result.score ?? '—'}</span>
                <span className="text-slate-400 text-[13px]">/ 100</span>
              </div>

              <p className="text-[13.5px] text-slate-600 bg-slate-50 border border-slate-200 rounded-lg px-4 py-3 mb-5.5">{result.reason}</p>

              <div className="grid grid-cols-2 gap-3 mb-5.5">
                <SubScoreCard name="Signature" value={result.sub_scores.signature} />
                <SubScoreCard name="Tamper" value={result.sub_scores.tamper} />
                <SubScoreCard name="OCR" value={result.sub_scores.ocr} />
                <SubScoreCard name="Anomaly" value={result.sub_scores.anomaly} />
              </div>

              {heatmapSrc && (
                <div className="mb-4">
                  <p className="text-[11.5px] font-semibold text-slate-400 mb-2">Tamper heatmap overlay</p>
                  <img src={heatmapSrc} className="w-full rounded-xl border border-slate-200" />
                </div>
              )}

              <details className="text-xs text-slate-400">
                <summary className="cursor-pointer font-semibold hover:text-slate-600">Raw response</summary>
                <pre className="mt-2.5 bg-slate-900 text-slate-100 rounded-lg p-3.5 overflow-x-auto font-mono text-[11px] leading-5">
                  {JSON.stringify(result, null, 2)}
                </pre>
              </details>
            </Card>
          ) : (
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-7 text-center">
              <div className="w-10 h-10 rounded-lg bg-brand-50 text-brand-600 flex items-center justify-center mx-auto mb-4">
                <svg width="19" height="19" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" /><path d="m9 12 2 2 4-4" /></svg>
              </div>
              <h3 className="text-[13.5px] font-bold text-slate-700 mb-1.5">Your result will appear here</h3>
              <p className="text-[12.5px] text-slate-400 leading-relaxed">
                Upload a document on the left. You'll get a 0–100 score, a plain-language reason,
                per-check sub-scores, and a tamper heatmap — right in this panel.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
