import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client.ts'
import type { SessionOut } from '../api/types.ts'
import SessionSidebar from '../components/SessionSidebar.tsx'

function byUpdatedDesc(a: SessionOut, b: SessionOut) {
  return Date.parse(b.updated_at) - Date.parse(a.updated_at)
}

function ChatPage() {
  const [sessions, setSessions] = useState<SessionOut[]>([])
  const [error, setError] = useState('')
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = Number(searchParams.get('session')) || null
  const selected = sessions.find((s) => s.id === selectedId)

  useEffect(() => {
    api
      .get<SessionOut[]>('/sessions')
      .then((list) => setSessions([...list].sort(byUpdatedDesc)))
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.message
            : '대화 목록을 불러오지 못했습니다.',
        ),
      )
  }, [])

  return (
    <div className="chat">
      <SessionSidebar
        sessions={sessions}
        selectedId={selectedId}
        onSelect={(id) => setSearchParams({ session: String(id) })}
      />
      <section>
        {error && <p className="error">{error}</p>}
        <h2>{selected ? selected.title : '새 대화'}</h2>
      </section>
    </div>
  )
}

export default ChatPage
