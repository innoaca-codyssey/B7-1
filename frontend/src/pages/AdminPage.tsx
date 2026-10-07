import { useSearchParams } from 'react-router-dom'

const TABS = [
  { key: 'users', label: '사용자' },
  { key: 'models', label: '모델' },
  { key: 'usage', label: '사용량' },
  { key: 'chats', label: '대화 로그' },
]

function AdminPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') ?? 'users'

  return (
    <>
      <h2>관리자</h2>
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            className={t.key === tab ? 'active' : ''}
            onClick={() => setSearchParams({ tab: t.key })}
          >
            {t.label}
          </button>
        ))}
      </nav>
    </>
  )
}

export default AdminPage
