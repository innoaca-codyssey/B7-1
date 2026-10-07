type Props = {
  offset: number
  limit: number
  total: number
  onChange: (offset: number) => void
}

function Pager({ offset, limit, total, onChange }: Props) {
  const pageCount = Math.max(1, Math.ceil(total / limit))

  return (
    <div className="pager">
      <button
        type="button"
        disabled={offset === 0}
        onClick={() => onChange(offset - limit)}
      >
        이전
      </button>
      <span>
        {offset / limit + 1} / {pageCount} (총 {total}건)
      </span>
      <button
        type="button"
        disabled={offset + limit >= total}
        onClick={() => onChange(offset + limit)}
      >
        다음
      </button>
    </div>
  )
}

export default Pager
