import { createContext, useContext } from 'react'
import type { UserOut } from '../api/types.ts'

export type AuthState = {
  user: UserOut | null
  loading: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth() {
  const auth = useContext(AuthContext)
  if (!auth) {
    throw new Error('AuthProvider 안에서만 사용할 수 있습니다.')
  }
  return auth
}
