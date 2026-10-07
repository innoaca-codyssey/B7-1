import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import type { ChatLogPage, UsageOut } from '../api/types.ts'
import ChatLogTable from '../components/ChatLogTable.tsx'
import Pager from '../components/Pager.tsx'
import UsageBar from '../components/UsageBar.tsx'

const LIMIT = 20

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

  return (
    <>
      <div className="page-header">
        <h2>내 대화 기록</h2>
        {usage && <UsageBar usage={usage} />}
      </div>
      {error && <p className="alert">{error}</p>}
      {page && (
        <>
          <ChatLogTable
            items={page.items}
            onRowClick={(item) => navigate(`/?session=${item.session_id}`)}
          />
          <Pager
            offset={offset}
            limit={LIMIT}
            total={page.total}
            onChange={setOffset}
          />
        </>
      )}
    </>
  )
}

export default LogsPage
