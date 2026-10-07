export class ApiError extends Error {
  status: number
  code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function toApiError(res: Response): Promise<ApiError> {
  if (res.status === 422) {
    return new ApiError(422, 'VALIDATION_ERROR', '입력값을 확인해 주세요.')
  }
  const body = await res.json().catch(() => null)
  const detail = body?.detail
  if (detail?.code) {
    return new ApiError(res.status, detail.code, detail.message)
  }
  return new ApiError(
    res.status,
    'UNKNOWN_ERROR',
    '요청을 처리하지 못했습니다.',
  )
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
): Promise<T> {
  let res: Response
  try {
    res = await fetch(`/api${path}`, {
      method,
      credentials: 'include',
      headers:
        body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError(0, 'NETWORK_ERROR', '서버에 연결할 수 없습니다.')
  }
  if (!res.ok) {
    throw await toApiError(res)
  }
  if (res.status === 204) {
    return undefined as T
  }
  return res.json()
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, body),
  patch: <T>(path: string, body?: unknown) => request<T>('PATCH', path, body),
  delete: <T = void>(path: string) => request<T>('DELETE', path),
}
