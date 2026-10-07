import type { UsageOut } from '../api/types.ts'

function UsageBar({ usage }: { usage: UsageOut }) {
  const percent = Math.min(100, (usage.month_used / usage.token_limit) * 100)

  return (
    <div className="usage">
      <div className="usage-bar">
        <div
          className={percent >= 90 ? 'over' : ''}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span>
        이번 달 {usage.month_used.toLocaleString()} /{' '}
        {usage.token_limit.toLocaleString()} 토큰
      </span>
    </div>
  )
}

export default UsageBar
