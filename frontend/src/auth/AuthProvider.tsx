import { useEffect, useState, type ReactNode } from 'react'
import { api } from '../api/client.ts'
import type { UserOut } from '../api/types.ts'
import { AuthContext } from './AuthContext.ts'

function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api
      .get<UserOut>('/auth/me')
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  async function login(username: string, password: string) {
    setUser(await api.post<UserOut>('/auth/login', { username, password }))
  }

  async function logout() {
    await api.post('/auth/logout').catch(() => {})
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export default AuthProvider
