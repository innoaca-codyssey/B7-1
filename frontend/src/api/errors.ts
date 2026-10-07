import { ApiError } from './client.ts'

const MESSAGES: Record<string, string> = {
  AI_TIMEOUT:
    'AI 응답이 지연되어 요청을 중단했습니다. 잠시 후 다시 시도해 주세요.',
  AI_ERROR: 'AI 서비스 호출에 실패했습니다. 잠시 후 다시 시도해 주세요.',
  QUOTA_EXCEEDED:
    '이번 달 사용 가능한 토큰을 모두 사용했습니다. 관리자에게 문의해 주세요.',
  MODEL_UNAVAILABLE:
    '선택한 모델을 사용할 수 없습니다. 다른 모델을 선택해 주세요.',
  NETWORK_ERROR: '서버에 연결할 수 없습니다. 네트워크 상태를 확인해 주세요.',
  VALIDATION_ERROR: '입력값을 확인해 주세요.',
  SELF_MODIFY: '자기 계정의 역할과 활성 상태는 변경할 수 없습니다.',
}

export function errorMessage(err: unknown, fallback: string) {
  if (!(err instanceof ApiError)) {
    return fallback
  }
  return MESSAGES[err.code] ?? err.message
}
