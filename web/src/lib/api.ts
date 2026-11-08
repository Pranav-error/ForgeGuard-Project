export interface AuthSession {
  token: string
  role: 'verifier' | 'admin'
  email: string
}

export interface SubScores {
  signature: number | null
  tamper: number | null
  ocr: number | null
  anomaly: number | null
}

export interface VerificationResult {
  document_id: string
  verification_id: string
  score: number | null
  label: 'Genuine' | 'Suspicious' | 'Forged' | 'Failed'
  reason: string
  sub_scores: SubScores
  tamper_regions: { bbox: number[]; confidence: number }[] | null
  signature_bbox: number[] | null
  ocr_fields: Record<string, string> | null
  anomaly_reconstruction_error: number | null
  ledger_block: { block_index: number; block_hash: string }
  heatmap_url: string | null
}

export interface HistoryRow {
  id: string
  document_id: string
  doc_type: string
  signature_sub_score: number | null
  tamper_sub_score: number | null
  ocr_sub_score: number | null
  anomaly_sub_score: number | null
  final_score: number | null
  label: string
  reason_text: string
  created_at: string
}

export interface AuditLogRow {
  id: string
  action: string
  verification_id: string | null
  detail_json: string
  created_at: string
}

class ApiError extends Error {}

function authHeaders(session: AuthSession | null): HeadersInit {
  return session ? { Authorization: `Bearer ${session.token}` } : {}
}

async function unwrap<T>(res: Response): Promise<T> {
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new ApiError(data.detail || `Request failed (${res.status})`)
  return data as T
}

export const api = {
  async register(email: string, password: string) {
    const fd = new FormData()
    fd.set('email', email)
    fd.set('password', password)
    return unwrap<{ id: string; email: string; role: string }>(await fetch('/auth/register', { method: 'POST', body: fd }))
  },

  async login(email: string, password: string) {
    const fd = new FormData()
    fd.set('email', email)
    fd.set('password', password)
    return unwrap<AuthSession>(await fetch('/auth/login', { method: 'POST', body: fd }))
  },

  async registerSignature(session: AuthSession, signerId: string, image: File) {
    const fd = new FormData()
    fd.set('signer_id', signerId)
    fd.set('image', image)
    return unwrap<{ id: string; signer_id: string }>(
      await fetch('/signatures', { method: 'POST', body: fd, headers: authHeaders(session) }),
    )
  },

  async verifyDocument(session: AuthSession, file: File, docType: string, signerId: string) {
    const fd = new FormData()
    fd.set('file', file)
    fd.set('doc_type', docType)
    if (signerId) fd.set('signer_id', signerId)
    return unwrap<VerificationResult>(
      await fetch('/documents', { method: 'POST', body: fd, headers: authHeaders(session) }),
    )
  },

  async fetchHeatmap(session: AuthSession, url: string) {
    const res = await fetch(url, { headers: authHeaders(session) })
    if (!res.ok) throw new ApiError('Could not load heatmap')
    return URL.createObjectURL(await res.blob())
  },

  async history(session: AuthSession) {
    return unwrap<HistoryRow[]>(await fetch('/verifications', { headers: authHeaders(session) }))
  },

  async auditLog(session: AuthSession) {
    return unwrap<AuditLogRow[]>(await fetch('/admin/audit-log', { headers: authHeaders(session) }))
  },

  async verifyLedger(session: AuthSession) {
    return unwrap<{ valid: boolean; length: number; broken_at: number | null }>(
      await fetch('/admin/ledger/verify', { headers: authHeaders(session) }),
    )
  },
}

export { ApiError }
