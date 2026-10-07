import { useState, type KeyboardEvent } from 'react'

const MAX_LENGTH = 4000

type Props = {
  sending: boolean
  onSend: (message: string) => Promise<boolean>
}

function ChatInput({ sending, onSend }: Props) {
  const [text, setText] = useState('')
  const length = [...text.trim()].length
  const canSend = !sending && length > 0 && length <= MAX_LENGTH

  async function submit() {
    if (!canSend) {
      return
    }
    const message = text.trim()
    setText('')
    if (!(await onSend(message))) {
      setText(text)
    }
  }

  function handleKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  return (
    <form
      className="chat-input"
      onSubmit={(e) => {
        e.preventDefault()
        submit()
      }}
    >
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="질문을 입력하세요. Shift+Enter로 줄바꿈"
        rows={3}
        disabled={sending}
      />
      <div className="chat-input-side">
        <span className={length > MAX_LENGTH ? 'counter error' : 'counter'}>
          {length}/{MAX_LENGTH}
        </span>
        <button type="submit" className="primary" disabled={!canSend}>
          전송
        </button>
      </div>
    </form>
  )
}

export default ChatInput
