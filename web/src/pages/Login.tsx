import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../lib/api'
import { useAuth } from '../lib/auth'
import { Card, inputClass, Msg, PrimaryButton } from '../components/ui'

export function Login() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)
  const { signIn } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setNotice(null)
    setLoading(true)
    try {
      if (mode === 'register') {
        await api.register(email, password)
        setNotice('Account created — now sign in.')
        setMode('login')
      } else {
        const session = await api.login(email, password)
        signIn(session)
        navigate('/dashboard')
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-md mx-auto px-5 py-20">
      <Link to="/" className="flex items-center gap-2.5 font-extrabold text-[15px] text-slate-900 mb-8 no-underline justify-center">
        <span className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" />
            <path d="m9 12 2 2 4-4" />
          </svg>
        </span>
        ForgeGuard
      </Link>

      <Card>
        <div className="inline-flex bg-slate-100 rounded-lg p-1 mb-5">
          {(['login', 'register'] as const).map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => {
                setMode(m)
                setError(null)
                setNotice(null)
              }}
              className={`text-[13px] font-semibold px-4 py-[7px] rounded-[7px] ${
                mode === m ? 'bg-white text-brand-600 shadow-sm' : 'text-slate-500'
              }`}
            >
              {m === 'login' ? 'Sign in' : 'Create account'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Email</label>
            <input
              type="email"
              required
              className={inputClass}
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="mb-4">
            <label className="block text-xs font-semibold text-slate-600 mb-1.5">Password</label>
            <input
              type="password"
              required
              className={inputClass}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <PrimaryButton type="submit" loading={loading} loadingText={mode === 'login' ? 'Signing in…' : 'Creating…'}>
            {mode === 'login' ? 'Sign in' : 'Create account'}
          </PrimaryButton>
        </form>

        {error && <Msg kind="err">{error}</Msg>}
        {notice && <Msg kind="ok">{notice}</Msg>}
      </Card>
    </div>
  )
}
