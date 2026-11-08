import { useState } from 'react'
import { api, ApiError, type VerificationResult } from '../lib/api'
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

  return (
    <div className="max-w-3xl mx-auto px-5">
      <div className="py-9">
        <h1 className="text-[22px] font-extrabold tracking-tight mb-1.5">Verify a document</h1>
        <p className="text-[13.5px] text-slate-500">Register a reference signature, then upload a document to run the full pipeline.</p>
      </div>

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

      {result && (
        <Card>
          <CardHead title="Result" />
          <div className="flex items-baseline gap-3 mb-4.5">
            <LabelPill label={result.label} />
            <span className={`text-[32px] font-extrabold tracking-tight ${scoreColor(result.label)}`}>{result.score ?? '—'}</span>
            <span className="text-slate-400 text-[13px]">/ 100</span>
          </div>

          <p className="text-[13.5px] text-slate-600 bg-slate-50 border border-slate-200 rounded-[10px] px-4 py-3 mb-5.5">{result.reason}</p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5.5">
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
            <pre className="mt-2.5 bg-slate-900 text-slate-100 rounded-[10px] p-3.5 overflow-x-auto font-mono text-[11px] leading-5">
              {JSON.stringify(result, null, 2)}
            </pre>
          </details>
        </Card>
      )}
    </div>
  )
}
