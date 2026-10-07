import type { ChatLogItem } from '../api/types.ts'

type Item = ChatLogItem & { username?: string }

type Props = {
  items: Item[]
  showUser?: boolean
  onRowClick?: (item: Item) => void
}

function summary(text: string, max: number) {
  const line = text.replace(/\s+/g, ' ').trim()
  return line.length > max ? `${line.slice(0, max)}...` : line
}

function ChatLogTable({ items, showUser = false, onRowClick }: Props) {
  return (
    <>
      <table className={onRowClick ? 'logs clickable' : 'logs'}>
        <thead>
          <tr>
            <th>시각</th>
            {showUser && <th>사용자</th>}
            <th>대화</th>
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
              {showUser && <td>{item.username}</td>}
              <td>{item.session_title}</td>
              <td>{summary(item.question, 40)}</td>
              <td>
                {item.answer === null ? '응답 없음' : summary(item.answer, 60)}
              </td>
              <td>
                {item.status === 'error' ? (
                  <span className="badge off">{item.error_code ?? '오류'}</span>
                ) : (
                  <span className="badge ok">정상</span>
                )}
              </td>
              <td className="nowrap">{item.model_code}</td>
              <td>{item.billed_tokens.toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {items.length === 0 && <p>대화 기록이 없습니다.</p>}
    </>
  )
}

export default ChatLogTable
