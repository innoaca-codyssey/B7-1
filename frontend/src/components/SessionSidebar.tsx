import type { SessionOut } from '../api/types.ts'

type Props = {
  sessions: SessionOut[]
  selectedId: number | null
  onSelect: (id: number) => void
}

function SessionSidebar({ sessions, selectedId, onSelect }: Props) {
  return (
    <aside className="sidebar">
      <ul>
        {sessions.map((s) => (
          <li key={s.id} className={s.id === selectedId ? 'selected' : ''}>
            <button type="button" onClick={() => onSelect(s.id)}>
              {s.title}
            </button>
          </li>
        ))}
      </ul>
      {sessions.length === 0 && <p>대화가 없습니다.</p>}
    </aside>
  )
}

export default SessionSidebar
