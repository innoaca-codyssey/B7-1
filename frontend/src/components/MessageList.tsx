import { useEffect, useRef } from 'react'
import Markdown from 'react-markdown'
import type { MessageOut } from '../api/types.ts'

type Props = {
  messages: MessageOut[]
  pending: string | null
}

function MessageList({ messages, pending }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView()
  }, [messages, pending])

  return (
    <div className="messages">
      {messages.length === 0 && pending === null && (
        <p className="empty">질문을 입력해 대화를 시작하세요.</p>
      )}
      {messages.map((m) => (
        <div key={m.id} className={`message ${m.role} ${m.status}`}>
          {m.role === 'assistant' && m.status === 'ok' ? (
            <>
              <Markdown>{m.content}</Markdown>
              <small>토큰 {m.billed_tokens}</small>
            </>
          ) : (
            <>
              <div>{m.content}</div>
              {m.error_code && <small>{m.error_code}</small>}
            </>
          )}
        </div>
      ))}
      {pending !== null && (
        <>
          <div className="message user">
            <div>{pending}</div>
          </div>
          <div className="message assistant pending">
            답변을 생성하고 있습니다...
          </div>
        </>
      )}
      <div ref={endRef} />
    </div>
  )
}

export default MessageList
