import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Sidebar } from './Sidebar'

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex">
      <Sidebar />
      <main className="flex-1 min-w-0">{children}</main>
    </div>
  )
}

export function ProtectedRoute() {
  const { session } = useAuth()
  if (!session) return <Navigate to="/login" replace />
  return (
    <Shell>
      <Outlet />
    </Shell>
  )
}

export function AdminRoute() {
  const { session } = useAuth()
  if (!session) return <Navigate to="/login" replace />
  if (session.role !== 'admin') {
    return (
      <Shell>
        <div className="max-w-3xl mx-auto px-5 py-16 text-center text-slate-500 text-sm">
          This page is for administrators only.
        </div>
      </Shell>
    )
  }
  return (
    <Shell>
      <Outlet />
    </Shell>
  )
}
