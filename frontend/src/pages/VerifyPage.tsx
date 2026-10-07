import { useEffect, useState, type FormEvent } from 'react'
import {
  Link,
  useLocation,
  useNavigate,
  useSearchParams,
} from 'react-router-dom'
import { api, ApiError } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'

const RESEND_SECONDS = 60

function VerifyPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const username = searchParams.get('username') ?? ''
  const fromSignup = Boolean(
    (useLocation().state as { fromSignup?: boolean } | null)?.fromSignup,
  )
  const [code, setCode] = useState('')
  const [error, setError] = useState('')
  const [notice, setNotice] = useState(
    fromSignup ? '가입한 이메일로 인증 코드를 보냈습니다.' : '',
  )
  const [submitting, setSubmitting] = useState(false)
  const [cooldown, setCooldown] = useState(fromSignup ? RESEND_SECONDS : 0)

  useEffect(() => {
    if (cooldown <= 0) {
      return
    }
    const timer = setTimeout(() => setCooldown(cooldown - 1), 1000)
    return () => clearTimeout(timer)
  }, [cooldown])

  if (!username) {
    return (
      <div className="auth-form">
        <h2>이메일 인증</h2>
        <p className="alert" role="alert">
          인증할 아이디 정보가 없습니다.
        </p>
        <p>
          <Link to="/login">로그인</Link>에서 다시 시도해 주세요.
        </p>
      </div>
    )
  }

  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await api.post('/auth/verify-email', { username, code })
      navigate('/login', {
        state: { notice: '이메일 인증이 완료되었습니다. 로그인해 주세요.' },
      })
    } catch (err) {
      setError(errorMessage(err, '인증하지 못했습니다.'))
      if (err instanceof ApiError && err.code === 'TOO_MANY_ATTEMPTS') {
        setCode('')
      }
      setSubmitting(false)
    }
  }

  async function handleResend() {
    setError('')
    setNotice('')
    try {
      await api.post('/auth/resend-code', { username })
      setNotice('인증 코드를 다시 보냈습니다.')
      setCooldown(RESEND_SECONDS)
    } catch (err) {
      setError(errorMessage(err, '인증 코드를 보내지 못했습니다.'))
      if (err instanceof ApiError && err.code === 'TOO_MANY_REQUESTS') {
        setCooldown(RESEND_SECONDS)
      }
    }
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit}>
      <h2>이메일 인증</h2>
      <p className="hint">
        <strong>{username}</strong> 계정의 이메일로 받은 6자리 코드를
        입력하세요.
      </p>
      <label>
        인증 코드
        <input
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={6}
        />
      </label>
      {notice && !error && <p className="notice">{notice}</p>}
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
      <button
        type="submit"
        className="primary"
        disabled={submitting || code.length !== 6}
      >
        인증하기
      </button>
      <button type="button" disabled={cooldown > 0} onClick={handleResend}>
        {cooldown > 0 ? `코드 다시 받기 (${cooldown}초)` : '코드 다시 받기'}
      </button>
      <p>
        <Link to="/login">로그인으로 돌아가기</Link>
      </p>
    </form>
  )
}

export default VerifyPage
