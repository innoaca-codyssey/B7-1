import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client.ts'
import type { ChatResponse, MessageOut, SessionOut } from '../api/types.ts'
import ChatInput from '../components/ChatInput.tsx'
import MessageList from '../components/MessageList.tsx'
import SessionSidebar from '../components/SessionSidebar.tsx'

function byUpdatedDesc(a: SessionOut, b: SessionOut) {
  return Date.parse(b.updated_at) - Date.parse(a.updated_at)
}

async function fetchSessions() {
  const list = await api.get<SessionOut[]>('/sessions')
  return [...list].sort(byUpdatedDesc)
}

function ChatPage() {
  const [sessions, setSessions] = useState<SessionOut[]>([])
  const [error, setError] = useState('')
  const [pending, setPending] = useState<string | null>(null)
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedId = Number(searchParams.get('session')) || null
  const selected = sessions.find((s) => s.id === selectedId)
  const [loaded, setLoaded] = useState<{
    sessionId: number
    messages: MessageOut[]
  } | null>(null)
  const messages =
    selectedId !== null && loaded?.sessionId === selectedId
      ? loaded.messages
      : []

  useEffect(() => {
    fetchSessions()
      .then(setSessions)
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.message
            : '대화 목록을 불러오지 못했습니다.',
        ),
      )
  }, [])

  useEffect(() => {
    if (selectedId === null) {
      return
    }
    let ignore = false
    api
      .get<MessageOut[]>(`/sessions/${selectedId}/messages`)
      .then((list) => {
        if (!ignore) {
          setLoaded({ sessionId: selectedId, messages: list })
        }
      })
      .catch((err) =>
        setError(
          err instanceof ApiError
            ? err.message
            : '메시지를 불러오지 못했습니다.',
        ),
      )
    return () => {
      ignore = true
    }
  }, [selectedId])

  function showError(err: unknown, fallback: string) {
    setError(err instanceof ApiError ? err.message : fallback)
  }

  async function handleCreate() {
    setError('')
    try {
      const session = await api.post<SessionOut>('/sessions', {})
      setSessions((prev) => [session, ...prev])
      setSearchParams({ session: String(session.id) })
    } catch (err) {
      showError(err, '새 대화를 만들지 못했습니다.')
    }
  }

  async function handleDelete(id: number) {
    setError('')
    try {
      await api.delete(`/sessions/${id}`)
      setSessions((prev) => prev.filter((s) => s.id !== id))
      if (id === selectedId) {
        setSearchParams({})
      }
    } catch (err) {
      showError(err, '대화를 삭제하지 못했습니다.')
    }
  }

  async function handleSend(message: string) {
    setError('')
    setPending(message)
    try {
      const res = await api.post<ChatResponse>('/chat', {
        session_id: selectedId ?? undefined,
        message,
      })
      setLoaded({
        sessionId: res.session_id,
        messages: [...messages, res.user_message, res.assistant_message],
      })
      if (res.session_id !== selectedId) {
        setSearchParams({ session: String(res.session_id) })
      }
      fetchSessions()
        .then(setSessions)
        .catch((err) => showError(err, '대화 목록을 불러오지 못했습니다.'))
      return true
    } catch (err) {
      showError(err, '메시지를 보내지 못했습니다.')
      return false
    } finally {
      setPending(null)
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
        <MessageList messages={messages} pending={pending} />
        <ChatInput sending={pending !== null} onSend={handleSend} />
      </section>
    </div>
  )
}

export default ChatPage
