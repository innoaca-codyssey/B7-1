import { useEffect, useState } from 'react'
import { api } from '../api/client.ts'
import { errorMessage } from '../api/errors.ts'
import type { AdminUserOut, Role, UserOut } from '../api/types.ts'
import { useAuth } from '../auth/AuthContext.ts'

type UserPatch = Partial<Pick<UserOut, 'role' | 'is_active' | 'token_limit'>>

function UserRow({
  user,
  isSelf,
  onSave,
}: {
  user: AdminUserOut
  isSelf: boolean
  onSave: (patch: UserPatch) => Promise<void>
}) {
  const [limit, setLimit] = useState(String(user.token_limit))
  const [saving, setSaving] = useState(false)
  const limitValue = Number(limit)
  const limitChanged =
    limit.trim() !== '' &&
    Number.isInteger(limitValue) &&
    limitValue >= 0 &&
    limitValue !== user.token_limit

  async function save(patch: UserPatch) {
    setSaving(true)
    try {
      await onSave(patch)
    } finally {
      setSaving(false)
    }
  }

  return (
    <tr>
      <td>{user.name}</td>
      <td>
        {user.username}
        {isSelf && ' (나)'}
      </td>
      <td>{user.email ?? '-'}</td>
      <td>
        <select
          value={user.role}
          disabled={saving || isSelf}
          onChange={(e) => save({ role: e.target.value as Role })}
        >
          <option value="user">user</option>
          <option value="admin">admin</option>
        </select>
      </td>
      <td className="nowrap">
        {user.email_verified_at === null && (
          <>
            <span className="badge warn">미인증</span>{' '}
          </>
        )}
        <span className={user.is_active ? 'badge ok' : 'badge off'}>
          {user.is_active ? '활성' : '비활성'}
        </span>{' '}
        <button
          type="button"
          disabled={saving || isSelf}
          onClick={() => save({ is_active: !user.is_active })}
        >
          {user.is_active ? '비활성화' : '활성화'}
        </button>
      </td>
      <td className="nowrap">
        {user.month_used.toLocaleString()} /{' '}
        <input
          type="number"
          min={0}
          value={limit}
          onChange={(e) => setLimit(e.target.value)}
        />{' '}
        <button
          type="button"
          disabled={saving || !limitChanged}
          onClick={() => save({ token_limit: limitValue })}
        >
          저장
        </button>
      </td>
      <td>{user.session_count}</td>
      <td className="nowrap">
        {new Date(user.created_at).toLocaleDateString('ko-KR')}
      </td>
    </tr>
  )
}

function UsersTab() {
  const { user: me } = useAuth()
  const [users, setUsers] = useState<AdminUserOut[]>([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get<AdminUserOut[]>('/admin/users')
      .then(setUsers)
      .catch((err) =>
        setError(errorMessage(err, '사용자 목록을 불러오지 못했습니다.')),
      )
  }, [])

  async function update(id: number, patch: UserPatch) {
    setError('')
    try {
      const updated = await api.patch<AdminUserOut>(`/admin/users/${id}`, patch)
      setUsers((prev) => prev.map((u) => (u.id === id ? updated : u)))
    } catch (err) {
      setError(errorMessage(err, '사용자 정보를 변경하지 못했습니다.'))
    }
  }

  return (
    <>
      {error && (
        <p className="alert" role="alert">
          {error}
        </p>
      )}
      <table className="logs">
        <thead>
          <tr>
            <th>이름</th>
            <th>아이디</th>
            <th>이메일</th>
            <th>역할</th>
            <th>상태</th>
            <th>이번 달 사용량 / 할당량</th>
            <th>대화 수</th>
            <th>가입일</th>
          </tr>
        </thead>
        <tbody>
          {users.map((u) => (
            <UserRow
              key={u.id}
              user={u}
              isSelf={u.id === me?.id}
              onSave={(patch) => update(u.id, patch)}
            />
          ))}
        </tbody>
      </table>
    </>
  )
}

export default UsersTab
