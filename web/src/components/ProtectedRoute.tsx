import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../lib/auth'
import { Nav } from './Nav'

export function ProtectedRoute() {
  const { session } = useAuth()
  if (!session) return <Navigate to="/login" replace />
  return (
    <>
      <Nav />
      <Outlet />
    </>
  )
}

export function AdminRoute() {
  const { session } = useAuth()
  if (!session) return <Navigate to="/login" replace />
  if (session.role !== 'admin') {
    return (
      <>
        <Nav />
        <div className="max-w-3xl mx-auto px-5 py-16 text-center text-slate-500 text-sm">
          This page is for administrators only.
        </div>
      </>
    )
  }
  return (
    <>
      <Nav />
      <Outlet />
    </>
  )
}
