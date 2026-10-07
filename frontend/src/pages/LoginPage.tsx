import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import { ApiError } from '../api/client.ts'
import { useAuth } from '../auth/AuthContext.ts'

function LoginPage() {
  const { user, login } = useAuth()
  const notice = (useLocation().state as { notice?: string } | null)?.notice
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(username, password)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : '로그인에 실패했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>로그인</h2>
      <label>
        아이디
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
          required
        />
      </label>
      <label>
        비밀번호
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
          required
        />
      </label>
      {notice && !error && <p>{notice}</p>}
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={submitting}>
        로그인
      </button>
      <p>
        계정이 없으면 <Link to="/signup">회원가입</Link>
      </p>
    </form>
  )
}

export default LoginPage
