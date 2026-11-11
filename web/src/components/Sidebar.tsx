import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Logo } from './ui'

const ICONS: Record<string, React.ReactNode> = {
  Dashboard: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><rect x="3" y="3" width="7" height="9" rx="1.5" /><rect x="14" y="3" width="7" height="5" rx="1.5" /><rect x="14" y="12" width="7" height="9" rx="1.5" /><rect x="3" y="16" width="7" height="5" rx="1.5" /></svg>
  ),
  Verify: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" /><path d="m9 12 2 2 4-4" /></svg>
  ),
  History: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 3" /></svg>
  ),
  Analytics: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M3 3v18h18" /><path d="M18 17V9" /><path d="M13 17V5" /><path d="M8 17v-3" /></svg>
  ),
  Admin: (
    <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4" /><path d="M4 21c0-4 3.6-7 8-7s8 3 8 7" /></svg>
  ),
}

const LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/verify', label: 'Verify' },
  { to: '/history', label: 'History' },
  { to: '/analytics', label: 'Analytics' },
]

export function Sidebar() {
  const { session, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const links = session?.role === 'admin' ? [...LINKS, { to: '/admin', label: 'Admin' }] : LINKS

  return (
    <aside className="w-60 shrink-0 border-r border-slate-200 bg-white/70 backdrop-blur-sm flex flex-col h-screen sticky top-0">
      <Link to="/dashboard" className="flex items-center px-5 h-16 border-b border-slate-200 no-underline shrink-0">
        <Logo size={26} />
      </Link>

      <Link
        to="/verify"
        className="mx-4 mt-4 inline-flex items-center justify-center gap-2 font-semibold text-[13px] rounded-lg px-4 py-2.5 text-white bg-brand-600 hover:bg-brand-700 no-underline"
      >
        + New verification
      </Link>

      <nav className="flex-1 px-3 py-5 space-y-0.5">
        {links.map((l) => {
          const active = location.pathname === l.to
          return (
            <Link
              key={l.to}
              to={l.to}
              className={`relative flex items-center gap-2.5 text-[13.5px] font-semibold pl-4 pr-3 py-2.5 rounded-lg no-underline ${
                active ? 'text-slate-900 bg-brand-50' : 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
              }`}
            >
              {active && <span className="absolute left-0 top-1.5 bottom-1.5 w-[3px] bg-gold-500 rounded-full" />}
              <span className={active ? 'text-brand-600' : 'text-slate-400'}>{ICONS[l.label]}</span>
              {l.label}
            </Link>
          )
        })}
      </nav>

      <div className="px-4 py-4 border-t border-slate-200 shrink-0">
        <div className="text-[12px] font-semibold text-slate-700 truncate">{session?.email}</div>
        <div className="flex items-center justify-between mt-0.5">
          <span className="text-[11px] text-slate-400 capitalize">{session?.role}</span>
          <button
            onClick={() => {
              signOut()
              navigate('/login')
            }}
            className="text-[11px] font-semibold text-slate-400 hover:text-slate-700"
          >
            Sign out
          </button>
        </div>
      </div>
    </aside>
  )
}
