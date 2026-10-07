import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api, ApiError } from '../api/client.ts'
import { useAuth } from '../auth/AuthContext.ts'

function validate(username: string, password: string) {
  if (!/^[a-z0-9_]{3,30}$/.test(username)) {
    return '아이디는 영문 소문자, 숫자, 밑줄(_)로 3~30자입니다.'
  }
  if (password.length < 8 || password.length > 72) {
    return '비밀번호는 8~72자입니다.'
  }
  if (new TextEncoder().encode(password).length > 72) {
    return '비밀번호는 72바이트 이하입니다. 한글은 한 글자에 3바이트입니다.'
  }
  return ''
}

function SignupPage() {
  const { user, login } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const message = validate(username, password)
    setError(message)
    if (message) {
      return
    }
    setSubmitting(true)
    try {
      await api.post('/auth/signup', { username, password })
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : '회원가입에 실패했습니다.',
      )
      setSubmitting(false)
      return
    }
    try {
      await login(username, password)
    } catch {
      navigate('/login', {
        state: { notice: '가입이 완료되었습니다. 로그인해 주세요.' },
      })
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>회원가입</h2>
      <label>
        아이디
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
        />
      </label>
      <label>
        비밀번호
        <input
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
      </label>
      {error && <p className="alert">{error}</p>}
      <button type="submit" className="primary" disabled={submitting}>
        가입하기
      </button>
      <p>
        이미 계정이 있으면 <Link to="/login">로그인</Link>
      </p>
    </form>
  )
}

export default SignupPage
