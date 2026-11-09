import { Link } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const LINKS = [
  {
    to: '/verify',
    title: 'Verify a document',
    body: 'Register a reference signature and run the full 5-service pipeline on an upload.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" /><path d="m9 12 2 2 4-4" /></svg>
    ),
  },
  {
    to: '/history',
    title: 'History',
    body: 'Every document you have verified, with its score, label and reason.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></svg>
    ),
  },
  {
    to: '/analytics',
    title: 'Analytics',
    body: 'Label breakdown, score averages, and a 14-day activity chart.',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" /></svg>
    ),
  },
]

export function Dashboard() {
  const { session } = useAuth()

  return (
    <div className="max-w-3xl mx-auto px-5">
      <div className="py-9">
        <h1 className="text-[22px] font-extrabold tracking-tight mb-1.5">Welcome back</h1>
        <p className="text-[13.5px] text-slate-500">
          Signed in as {session?.email} · {session?.role}
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {LINKS.map((l) => (
          <Link
            key={l.to}
            to={l.to}
            className="block bg-white border border-slate-200 rounded-2xl p-5 hover:border-brand-600 hover:shadow-[0_2px_8px_rgba(79,70,229,.08)] no-underline"
          >
            <div className="w-9 h-9 rounded-[10px] bg-brand-50 text-brand-600 flex items-center justify-center mb-3.5">{l.icon}</div>
            <h3 className="text-[14.5px] font-bold text-slate-800 mb-1">{l.title}</h3>
            <p className="text-[12.5px] text-slate-500 m-0">{l.body}</p>
          </Link>
        ))}
        {session?.role === 'admin' && (
          <Link
            to="/admin"
            className="block bg-white border border-slate-200 rounded-2xl p-5 hover:border-brand-600 hover:shadow-[0_2px_8px_rgba(79,70,229,.08)] no-underline"
          >
            <div className="w-9 h-9 rounded-[10px] bg-brand-50 text-brand-600 flex items-center justify-center mb-3.5">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" />
              </svg>
            </div>
            <h3 className="text-[14.5px] font-bold text-slate-800 mb-1">Admin</h3>
            <p className="text-[12.5px] text-slate-500 m-0">Audit log and the hash-chain ledger's integrity check.</p>
          </Link>
        )}
      </div>
    </div>
  )
}
