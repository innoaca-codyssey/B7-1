import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api, ApiError } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
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
  const [sessionsLoaded, setSessionsLoaded] = useState(false)
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
    selected && loaded?.sessionId === selected.id ? loaded.messages : []

  useEffect(() => {
    fetchSessions()
      .then((list) => {
        setSessions(list)
        setSessionsLoaded(true)
      })
      .catch((err) =>
        setError(errorMessage(err, '대화 목록을 불러오지 못했습니다.')),
      )
  }, [])

  useEffect(() => {
    if (sessionsLoaded && selectedId !== null && !selected) {
      setSearchParams({}, { replace: true })
    }
  }, [sessionsLoaded, selectedId, selected, setSearchParams])

  const loadId = selected ? selected.id : null

  useEffect(() => {
    if (loadId === null) {
      return
    }
    let ignore = false
    api
      .get<MessageOut[]>(`/sessions/${loadId}/messages`)
      .then((list) => {
        if (!ignore) {
          setLoaded({ sessionId: loadId, messages: list })
        }
      })
      .catch((err) =>
        setError(errorMessage(err, '메시지를 불러오지 못했습니다.')),
      )
    return () => {
      ignore = true
    }
  }, [loadId])

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

  async function showSavedMessages(sessionId: number) {
    try {
      const [list, saved] = await Promise.all([
        fetchSessions(),
        api.get<MessageOut[]>(`/sessions/${sessionId}/messages`),
      ])
      setSessions(list)
      setLoaded({ sessionId, messages: saved })
      if (sessionId !== selectedId) {
        setSearchParams({ session: String(sessionId) })
      }
    } catch {
      // 원래 실패 안내를 유지한다
    }
  }

  async function handleSend(message: string) {
    setError('')
    setPending(message)
    let res: ChatResponse
    try {
      res = await api.post<ChatResponse>('/chat', {
        session_id: selected?.id,
        message,
      })
    } catch (err) {
      setError(errorMessage(err, '메시지를 보내지 못했습니다.'))
      if (err instanceof ApiError && err.sessionId !== null) {
        await showSavedMessages(err.sessionId)
      }
      setPending(null)
      return false
    }
    setLoaded({
      sessionId: res.session_id,
      messages: [...messages, res.user_message, res.assistant_message],
    })
    try {
      setSessions(await fetchSessions())
      if (res.session_id !== selectedId) {
        setSearchParams({ session: String(res.session_id) })
      }
    } catch (err) {
      setError(errorMessage(err, '대화 목록을 불러오지 못했습니다.'))
    }
    setPending(null)
    return true
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
