import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'

const LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/verify', label: 'Verify' },
  { to: '/history', label: 'History' },
]

export function Nav() {
  const { session, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const links = session?.role === 'admin' ? [...LINKS, { to: '/admin', label: 'Admin' }] : LINKS

  return (
    <div className="border-b border-slate-200 bg-white/75 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-5 py-3.5 flex items-center gap-7">
        <Link to="/dashboard" className="flex items-center gap-2.5 font-extrabold text-[15px] tracking-tight shrink-0 no-underline text-slate-900">
          <span className="w-7 h-7 rounded-lg bg-brand-600 flex items-center justify-center">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2 4 5v6c0 5.25 3.4 9.74 8 11 4.6-1.26 8-5.75 8-11V5l-8-3Z" />
              <path d="m9 12 2 2 4-4" />
            </svg>
          </span>
          ForgeGuard
        </Link>
        <div className="flex gap-1 flex-1 max-sm:hidden">
          {links.map((l) => (
            <Link
              key={l.to}
              to={l.to}
              className={`text-[13.5px] font-semibold px-3 py-1.5 rounded-lg no-underline ${
                location.pathname === l.to ? 'text-brand-600 bg-brand-50' : 'text-slate-500 hover:bg-slate-100'
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>
        <div className="flex items-center gap-3 text-[12.5px] text-slate-500 ml-auto">
          <span>
            {session?.email} <span className="text-slate-300">·</span> {session?.role}
          </span>
          <button
            onClick={() => {
              signOut()
              navigate('/login')
            }}
            className="font-semibold text-slate-500 hover:text-slate-800"
          >
            Sign out
          </button>
        </div>
      </div>
    </div>
  )
}
