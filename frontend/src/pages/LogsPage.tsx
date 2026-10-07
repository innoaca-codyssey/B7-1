import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import type { ChatLogPage, UsageOut } from '../api/types.ts'
import UsageBar from '../components/UsageBar.tsx'

const LIMIT = 20

function summary(text: string, max: number) {
  const line = text.replace(/\s+/g, ' ').trim()
  return line.length > max ? `${line.slice(0, max)}...` : line
}

function LogsPage() {
  const navigate = useNavigate()
  const [offset, setOffset] = useState(0)
  const [page, setPage] = useState<ChatLogPage | null>(null)
  const [usage, setUsage] = useState<UsageOut | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<UsageOut>('/me/usage')
      .then(setUsage)
      .catch(() => setUsage(null))
  }, [])

  useEffect(() => {
    let ignore = false
    api
      .get<ChatLogPage>(`/me/chats?limit=${LIMIT}&offset=${offset}`)
      .then((result) => {
        if (!ignore) {
          setPage(result)
        }
      })
      .catch((err) =>
        setError(errorMessage(err, '대화 기록을 불러오지 못했습니다.')),
      )
    return () => {
      ignore = true
    }
  }, [offset])

  const total = page?.total ?? 0
  const pageCount = Math.max(1, Math.ceil(total / LIMIT))
  const current = offset / LIMIT + 1

  return (
    <>
      <h2>내 대화 기록</h2>
      {usage && <UsageBar usage={usage} />}
      {error && <p className="error">{error}</p>}
      <table className="logs">
        <thead>
          <tr>
            <th>시각</th>
            <th>대화</th>
            <th>질문</th>
            <th>답변</th>
            <th>상태</th>
            <th>모델</th>
            <th>토큰</th>
          </tr>
        </thead>
        <tbody>
          {page?.items.map((item) => (
            <tr
              key={item.id}
              onClick={() => navigate(`/?session=${item.session_id}`)}
            >
              <td className="nowrap">
                {new Date(item.created_at).toLocaleString('ko-KR', {
                  dateStyle: 'short',
                  timeStyle: 'short',
                })}
              </td>
              <td>{item.session_title}</td>
              <td>{summary(item.question, 40)}</td>
              <td>{summary(item.answer, 60)}</td>
              <td className={item.status === 'error' ? 'error' : ''}>
                {item.status === 'error' ? item.error_code : '정상'}
              </td>
              <td className="nowrap">{item.model_code}</td>
              <td>{item.billed_tokens.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {page?.items.length === 0 && <p>대화 기록이 없습니다.</p>}
      <div className="pager">
        <button
          type="button"
          disabled={offset === 0}
          onClick={() => setOffset(offset - LIMIT)}
        >
          이전
        </button>
        <span>
          {current} / {pageCount} (총 {total}건)
        </span>
        <button
          type="button"
          disabled={offset + LIMIT >= total}
          onClick={() => setOffset(offset + LIMIT)}
        >
          다음
        </button>
      </div>
    </>
  )
}

export default LogsPage
