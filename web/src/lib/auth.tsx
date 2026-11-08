import { createContext, useContext, useState, type ReactNode } from 'react'
import type { AuthSession } from './api'

const STORAGE_KEY = 'forgeguard_auth'

function loadSession(): AuthSession | null {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY)
    return raw ? (JSON.parse(raw) as AuthSession) : null
  } catch {
    return null
  }
}

interface AuthContextValue {
  session: AuthSession | null
  signIn: (session: AuthSession) => void
  signOut: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<AuthSession | null>(loadSession)

  const signIn = (s: AuthSession) => {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(s))
    setSession(s)
  }
  const signOut = () => {
    sessionStorage.removeItem(STORAGE_KEY)
    setSession(null)
  }

  return <AuthContext.Provider value={{ session, signIn, signOut }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
