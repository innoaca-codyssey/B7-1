import { useEffect, useState } from 'react'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import type { DailyUsage } from '../api/types.ts'

const DAYS = 30

type Total = { key: string; requests: number; billed_tokens: number }

function sumBy(rows: DailyUsage[], key: 'date' | 'model_code') {
  const totals = new Map<string, Total>()
  for (const row of rows) {
    const total = totals.get(row[key]) ?? {
      key: row[key],
      requests: 0,
      billed_tokens: 0,
    }
    total.requests += row.requests
    total.billed_tokens += row.billed_tokens
    totals.set(row[key], total)
  }
  return [...totals.values()]
}

function TotalTable({ title, totals }: { title: string; totals: Total[] }) {
  const max = Math.max(1, ...totals.map((t) => t.billed_tokens))

  return (
    <table className="logs">
      <thead>
        <tr>
          <th>{title}</th>
          <th>요청 수</th>
          <th>토큰</th>
          <th />
        </tr>
      </thead>
      <tbody>
        {totals.map((t) => (
          <tr key={t.key}>
            <td className="nowrap">{t.key}</td>
            <td>{t.requests.toLocaleString()}</td>
            <td>{t.billed_tokens.toLocaleString()}</td>
            <td>
              <div className="usage-bar">
                <div style={{ width: `${(t.billed_tokens / max) * 100}%` }} />
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function UsageTab() {
  const [rows, setRows] = useState<DailyUsage[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<DailyUsage[]>(`/admin/usage?days=${DAYS}`)
      .then(setRows)
      .catch((err) =>
        setError(errorMessage(err, '사용량을 불러오지 못했습니다.')),
      )
  }, [])

  const byModel = sumBy(rows, 'model_code').sort(
    (a, b) => b.billed_tokens - a.billed_tokens,
  )
  const byDate = sumBy(rows, 'date').sort((a, b) => b.key.localeCompare(a.key))

  return (
    <>
      {error && <p className="alert">{error}</p>}
      <h3>최근 {DAYS}일 모델별 합계</h3>
      <TotalTable title="모델" totals={byModel} />
      <h3>일자별 합계</h3>
      <TotalTable title="날짜" totals={byDate} />
    </>
  )
}

export default UsageTab
