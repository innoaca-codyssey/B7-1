import { useState } from 'react'
import type { SessionOut } from '../api/types.ts'

type Props = {
  sessions: SessionOut[]
  selectedId: number | null
  onSelect: (id: number) => void
  onCreate: () => void
  onDelete: (id: number) => void
}

function SessionSidebar({
  sessions,
  selectedId,
  onSelect,
  onCreate,
  onDelete,
}: Props) {
  const [confirmingId, setConfirmingId] = useState<number | null>(null)

  return (
    <aside className="sidebar">
      <button type="button" className="primary" onClick={onCreate}>
        새 대화
      </button>
      <ul>
        {sessions.map((s) => (
          <li key={s.id} className={s.id === selectedId ? 'selected' : ''}>
            <button
              type="button"
              className="title"
              title={s.title}
              onClick={() => onSelect(s.id)}
            >
              {s.title}
            </button>
            {confirmingId === s.id ? (
              <>
                <button
                  type="button"
                  className="danger"
                  onClick={() => onDelete(s.id)}
                >
                  삭제
                </button>
                <button type="button" onClick={() => setConfirmingId(null)}>
                  취소
                </button>
              </>
            ) : (
              <button
                type="button"
                className="icon"
                aria-label="대화 삭제"
                onClick={() => setConfirmingId(s.id)}
              >
                x
              </button>
            )}
          </li>
        ))}
      </ul>
      {sessions.length === 0 && <p className="empty">대화가 없습니다.</p>}
    </aside>
  )
}

export default SessionSidebar
