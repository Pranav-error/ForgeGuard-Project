import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AdminRoute, ProtectedRoute } from './components/ProtectedRoute'
import { AuthProvider } from './lib/auth'
import { Admin } from './pages/Admin'
import { Analytics } from './pages/Analytics'
import { Dashboard } from './pages/Dashboard'
import { History } from './pages/History'
import { Landing } from './pages/Landing'
import { Login } from './pages/Login'
import { Verify } from './pages/Verify'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/verify" element={<Verify />} />
            <Route path="/history" element={<History />} />
            <Route path="/analytics" element={<Analytics />} />
          </Route>

          <Route element={<AdminRoute />}>
            <Route path="/admin" element={<Admin />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
