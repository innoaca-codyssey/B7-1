import type { ChatLogItem } from '../api/types.ts'

type Item = ChatLogItem & { username?: string; display_name?: string }

type Props = {
  items: Item[]
  showUser?: boolean
  onRowClick?: (item: Item) => void
}

function ChatLogTable({ items, showUser = false, onRowClick }: Props) {
  return (
    <>
      <table className={onRowClick ? 'logs clickable' : 'logs'}>
        <thead>
          <tr>
            <th>시각</th>
            {showUser && <th>사용자</th>}
            <th>질문</th>
            <th>답변</th>
            <th>상태</th>
            <th>모델</th>
            <th>토큰</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} onClick={() => onRowClick?.(item)}>
              <td className="nowrap">
                {new Date(item.created_at).toLocaleString('ko-KR', {
                  dateStyle: 'short',
                  timeStyle: 'short',
                })}
              </td>
              {showUser && (
                <td className="nowrap">
                  {item.display_name}({item.username})
                </td>
              )}
              <td
                className="ellipsis"
                title={`[${item.session_title}] ${item.question}`}
              >
                {item.question}
              </td>
              <td className="ellipsis" title={item.answer ?? undefined}>
                {item.answer ?? <span className="muted">응답 없음</span>}
              </td>
              <td className="nowrap">
                {item.status === 'error' ? (
                  <span className="badge off">{item.error_code ?? '오류'}</span>
                ) : (
                  <span className="badge ok">정상</span>
                )}
              </td>
              <td className="nowrap">{item.model_code}</td>
              <td className="nowrap">{item.billed_tokens.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p>대화 기록이 없습니다.</p>}
    </>
  )
}

export default ChatLogTable
