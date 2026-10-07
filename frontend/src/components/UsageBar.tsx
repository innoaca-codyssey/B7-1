import type { UsageOut } from '../api/types.ts'

function UsageBar({ usage }: { usage: UsageOut }) {
  const exceeded = usage.month_used >= usage.token_limit
  const percent = exceeded
    ? 100
    : Math.min(100, (usage.month_used / usage.token_limit) * 100)

  return (
    <div className="usage">
      <div className="usage-bar">
        <div
          className={percent >= 90 ? 'over' : ''}
          style={{
            width: usage.month_used > 0 ? `max(2px, ${percent}%)` : 0,
          }}
        />
      </div>
      <span>
        이번 달 {usage.month_used.toLocaleString()} /{' '}
        {usage.token_limit.toLocaleString()} 토큰
        {exceeded && <strong className="counter error"> 한도 초과</strong>}
      </span>
    </div>
  )
}

export default UsageBar
