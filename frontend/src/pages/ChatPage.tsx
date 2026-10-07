import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client.ts'
import type { SessionOut } from '../api/types.ts'
import SessionSidebar from '../components/SessionSidebar.tsx'

function byUpdatedDesc(a: SessionOut, b: SessionOut) {
  return Date.parse(b.updated_at) - Date.parse(a.updated_at)
}

function errorMessage(err: unknown, fallback: string) {
  return err instanceof ApiError ? err.message : fallback
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
        setError(errorMessage(err, '대화 목록을 불러오지 못했습니다.')),
      )
  }, [])

  async function handleCreate() {
    setError('')
    try {
      const session = await api.post<SessionOut>('/sessions', {})
      setSessions((prev) => [session, ...prev])
      setSearchParams({ session: String(session.id) })
    } catch (err) {
      setError(errorMessage(err, '새 대화를 만들지 못했습니다.'))
    }
  }

  async function handleDelete(id: number) {
    setError('')
    try {
      await api.delete(`/sessions/${id}`)
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 404)) {
        setError(errorMessage(err, '대화를 삭제하지 못했습니다.'))
        return
      }
    }
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (id === selectedId) {
      setSearchParams({})
    }
  }

  return (
    <div className="chat">
      <SessionSidebar
        sessions={sessions}
        selectedId={selectedId}
        onSelect={(id) => setSearchParams({ session: String(id) })}
        onCreate={handleCreate}
        onDelete={handleDelete}
      />
      <section>
        {error && <p className="error">{error}</p>}
        <h2>{selected ? selected.title : '새 대화'}</h2>
      </section>
    </div>
  )
}

export default ChatPage
