import { useEffect, useRef } from 'react'
import Markdown from 'react-markdown'
import type { MessageOut } from '../api/types.ts'

type Props = {
  messages: MessageOut[]
}

function MessageList({ messages }: Props) {
  const endRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    endRef.current?.scrollIntoView()
  }, [messages])

  return (
    <div className="messages">
      {messages.map((m) => (
        <div key={m.id} className={`message ${m.role} ${m.status}`}>
          {m.role === 'assistant' && m.status === 'ok' ? (
            <>
              <Markdown>{m.content}</Markdown>
              <small>토큰 {m.billed_tokens}</small>
            </>
          ) : (
            <div>{m.content}</div>
          )}
        </div>
      ))}
      <div ref={endRef} />
    </div>
  )
}

export default MessageList
