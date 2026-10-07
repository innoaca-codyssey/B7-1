import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import { useAuth } from '../auth/AuthContext.ts'

function validate(
  name: string,
  username: string,
  email: string,
  password: string,
) {
  const nameLength = [...name.trim()].length
  if (nameLength < 1 || nameLength > 30) {
    return '이름은 1~30자로 입력해 주세요.'
  }
  if (!/^[a-z0-9_]{3,30}$/.test(username)) {
    return '아이디는 영문 소문자, 숫자, 밑줄(_)로 3~30자입니다.'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return '이메일 형식을 확인해 주세요.'
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
  const { user } = useAuth()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) {
    return <Navigate to="/" replace />
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const message = validate(name, username, email.trim(), password)
    setError(message)
    if (message) {
      return
    }
    setSubmitting(true)
    try {
      await api.post('/auth/signup', {
        username,
        name: name.trim(),
        email: email.trim(),
        password,
      })
      navigate(`/verify?username=${encodeURIComponent(username)}`, {
        state: { fromSignup: true },
      })
    } catch (err) {
      setError(errorMessage(err, '회원가입에 실패했습니다.'))
      setSubmitting(false)
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <h2>회원가입</h2>
      <label>
        이름
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          autoComplete="name"
        />
      </label>
      <label>
        아이디
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          autoComplete="username"
        />
      </label>
      <label>
        이메일
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          autoComplete="email"
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
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
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
