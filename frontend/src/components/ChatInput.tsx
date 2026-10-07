import { useState, type KeyboardEvent } from 'react'

type Props = {
  sending: boolean
  onSend: (message: string) => Promise<boolean>
}

function ChatInput({ sending, onSend }: Props) {
  const [text, setText] = useState('')

  async function submit() {
    const message = text.trim()
    if (!message || sending) {
      return
    }
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
      <button type="submit" disabled={sending || !text.trim()}>
        전송
      </button>
    </form>
  )
}

export default ChatInput
