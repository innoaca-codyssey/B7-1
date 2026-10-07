import { useEffect, useState } from 'react'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import type { AdminModelOut } from '../api/types.ts'

type ModelPatch = Partial<
  Pick<
    AdminModelOut,
    'is_active' | 'is_default' | 'multiplier' | 'max_tokens' | 'sort_order'
  >
>

async function fetchModels() {
  const list = await api.get<AdminModelOut[]>('/admin/models')
  return [...list].sort((a, b) => a.sort_order - b.sort_order)
}

function ModelRow({
  model,
  onSave,
}: {
  model: AdminModelOut
  onSave: (patch: ModelPatch) => Promise<void>
}) {
  const [multiplier, setMultiplier] = useState(String(model.multiplier))
  const [maxTokens, setMaxTokens] = useState(String(model.max_tokens))
  const [sortOrder, setSortOrder] = useState(String(model.sort_order))
  const [saving, setSaving] = useState(false)

  const edits: ModelPatch = {}
  if (Number(multiplier) !== model.multiplier) {
    edits.multiplier = Number(multiplier)
  }
  if (Number(maxTokens) !== model.max_tokens) {
    edits.max_tokens = Number(maxTokens)
  }
  if (Number(sortOrder) !== model.sort_order) {
    edits.sort_order = Number(sortOrder)
  }
  const valid =
    Number(multiplier) > 0 &&
    Number.isInteger(Number(maxTokens)) &&
    Number(maxTokens) > 0 &&
    Number.isInteger(Number(sortOrder))
  const changed = Object.keys(edits).length > 0

  async function save(patch: ModelPatch) {
    setSaving(true)
    await onSave(patch)
    setSaving(false)
  }

  return (
    <tr>
      <td className="nowrap">{model.code}</td>
      <td>{model.name}</td>
      <td>{model.provider}</td>
      <td>
        <input
          type="number"
          step="0.1"
          min={0}
          value={multiplier}
          onChange={(e) => setMultiplier(e.target.value)}
        />
      </td>
      <td>
        <input
          type="number"
          min={1}
          value={maxTokens}
          onChange={(e) => setMaxTokens(e.target.value)}
        />
      </td>
      <td>
        <input
          type="number"
          value={sortOrder}
          onChange={(e) => setSortOrder(e.target.value)}
        />
      </td>
      <td className="nowrap">
        <span className={model.is_active ? '' : 'error'}>
          {model.is_active ? '활성' : '비활성'}
        </span>{' '}
        <button
          type="button"
          disabled={saving}
          onClick={() => save({ is_active: !model.is_active })}
        >
          {model.is_active ? '비활성화' : '활성화'}
        </button>
      </td>
      <td className="nowrap">
        {model.is_default ? (
          <strong>기본</strong>
        ) : (
          <button
            type="button"
            disabled={saving}
            onClick={() => save({ is_default: true })}
          >
            기본 지정
          </button>
        )}
      </td>
      <td>
        <button
          type="button"
          disabled={saving || !changed || !valid}
          onClick={() => save(edits)}
        >
          저장
        </button>
      </td>
    </tr>
  )
}

function ModelsTab() {
  const [models, setModels] = useState<AdminModelOut[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    fetchModels()
      .then(setModels)
      .catch((err) =>
        setError(errorMessage(err, '모델 목록을 불러오지 못했습니다.')),
      )
  }, [])

  async function update(code: string, patch: ModelPatch) {
    setError('')
    try {
      await api.patch(`/admin/models/${code}`, patch)
      setModels(await fetchModels())
    } catch (err) {
      setError(errorMessage(err, '모델 설정을 변경하지 못했습니다.'))
    }
  }

  return (
    <>
      {error && <p className="error">{error}</p>}
      <table className="logs">
        <thead>
          <tr>
            <th>코드</th>
            <th>이름</th>
            <th>제공사</th>
            <th>배율</th>
            <th>max_tokens</th>
            <th>순서</th>
            <th>상태</th>
            <th>기본</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {models.map((m) => (
            <ModelRow
              key={m.code}
              model={m}
              onSave={(patch) => update(m.code, patch)}
            />
          ))}
        </tbody>
      </table>
    </>
  )
}

export default ModelsTab
