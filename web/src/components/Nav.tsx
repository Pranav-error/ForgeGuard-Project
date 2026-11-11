import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Logo } from './ui'

const LINKS = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/verify', label: 'Verify' },
  { to: '/history', label: 'History' },
  { to: '/analytics', label: 'Analytics' },
]

export function Nav() {
  const { session, signOut } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()

  const links = session?.role === 'admin' ? [...LINKS, { to: '/admin', label: 'Admin' }] : LINKS

  return (
    <div className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-5 flex items-center gap-7">
        <Link to="/dashboard" className="flex items-center py-3.5 no-underline shrink-0">
          <Logo size={26} />
        </Link>
        <div className="flex gap-1 flex-1 max-sm:hidden self-stretch">
          {links.map((l) => {
            const active = location.pathname === l.to
            return (
              <Link
                key={l.to}
                to={l.to}
                className={`relative flex items-center text-[13.5px] font-semibold px-3 no-underline ${
                  active ? 'text-slate-900' : 'text-slate-500 hover:text-slate-800'
                }`}
              >
                {l.label}
                {active && <span className="absolute left-3 right-3 -bottom-px h-[2.5px] bg-gold-500 rounded-full" />}
              </Link>
            )
          })}
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
