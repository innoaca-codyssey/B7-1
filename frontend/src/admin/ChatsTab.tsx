import { useEffect, useState } from 'react'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import type { AdminChatLogPage, AdminUserOut } from '../api/types.ts'
import ChatLogTable from '../components/ChatLogTable.tsx'
import Pager from '../components/Pager.tsx'

const LIMIT = 20

function ChatsTab() {
  const [users, setUsers] = useState<AdminUserOut[]>([])
  const [userId, setUserId] = useState('')
  const [offset, setOffset] = useState(0)
  const [page, setPage] = useState<AdminChatLogPage | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<AdminUserOut[]>('/admin/users')
      .then(setUsers)
      .catch((err) =>
        setError(errorMessage(err, '사용자 목록을 불러오지 못했습니다.')),
      )
  }, [])

  useEffect(() => {
    const params = new URLSearchParams({
      limit: String(LIMIT),
      offset: String(offset),
    })
    if (userId) {
      params.set('user_id', userId)
    }
    let ignore = false
    api
      .get<AdminChatLogPage>(`/admin/chats?${params}`)
      .then((result) => {
        if (!ignore) {
          setPage(result)
        }
      })
      .catch((err) =>
        setError(errorMessage(err, '대화 로그를 불러오지 못했습니다.')),
      )
    return () => {
      ignore = true
    }
  }, [userId, offset])

  return (
    <>
      {error && <p className="error">{error}</p>}
      <label>
        사용자{' '}
        <select
          value={userId}
          onChange={(e) => {
            setUserId(e.target.value)
            setOffset(0)
          }}
        >
          <option value="">전체</option>
          {users.map((u) => (
            <option key={u.id} value={u.id}>
              {u.username}
            </option>
          ))}
        </select>
      </label>
      {page && (
        <>
          <ChatLogTable items={page.items} showUser />
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

export default ChatsTab
