import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext.ts'

function RequireAuth({ admin = false }: { admin?: boolean }) {
  const { user, loading } = useAuth()

  if (loading) {
    return null
  }
  if (!user) {
    return <Navigate to="/login" replace />
  }
  if (admin && user.role !== 'admin') {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}

export default RequireAuth
