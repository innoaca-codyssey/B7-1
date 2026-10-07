# API 명세

모든 API는 `/api`로 시작하며 요청과 응답 본문은 JSON입니다. 로그인하면 `access_token` 쿠키(HttpOnly, SameSite=Lax)가 발급되고, 인증이 필요한 API는 이 쿠키로 사용자를 확인합니다. 시각은 UTC 기준 ISO 8601 문자열입니다.

아래 응답 예시는 curl로 요청해 받은 출력입니다. 채팅 성공 응답과 일별 사용량은 운영 서버(https://chat.codyssey.run)에서, 나머지는 로컬 서버에서 받았습니다. AI 실패 응답은 `AI_BASE_URL`을 오류를 반환하는 서버로 바꿔 확인했습니다.

| 메서드 | 경로 | 인증 | 설명 |
|---|---|---|---|
| POST | `/api/auth/signup` | 없음 | 회원가입, 인증 코드 메일 발송 |
| POST | `/api/auth/verify-email` | 없음 | 이메일 인증 코드 확인 |
| POST | `/api/auth/resend-code` | 없음 | 인증 코드 재발송 |
| POST | `/api/auth/login` | 없음 | 로그인, 쿠키 발급 |
| POST | `/api/auth/logout` | 없음 | 쿠키 삭제 |
| GET | `/api/auth/me` | 로그인 | 내 정보 |
| GET | `/api/models` | 없음 | 사용 가능한 모델 목록 |
| GET | `/api/presets` | 없음 | 대화 프리셋 목록 |
| GET | `/api/sessions` | 로그인 | 내 대화 목록 |
| POST | `/api/sessions` | 로그인 | 대화 생성 |
| PATCH | `/api/sessions/{id}` | 로그인 | 대화 제목, 모델, 프리셋 변경 |
| DELETE | `/api/sessions/{id}` | 로그인 | 대화 삭제 |
| GET | `/api/sessions/{id}/messages` | 로그인 | 대화의 메시지 목록 |
| POST | `/api/chat` | 로그인 | 질문 전송, AI 응답 반환 |
| GET | `/api/me/chats` | 로그인 | 내 질문과 답변 기록 |
| GET | `/api/me/usage` | 로그인 | 이번 달 토큰 사용량 |
| GET | `/api/admin/users` | 관리자 | 사용자 목록과 사용량 |
| PATCH | `/api/admin/users/{id}` | 관리자 | 권한, 활성 여부, 토큰 한도 변경 |
| GET | `/api/admin/chats` | 관리자 | 전체 또는 사용자별 대화 기록 |
| GET | `/api/admin/models` | 관리자 | 전체 모델 목록 |
| PATCH | `/api/admin/models/{code}` | 관리자 | 모델 설정 변경 |
| GET | `/api/admin/usage` | 관리자 | 일별, 모델별 사용량 |

## 에러 응답

직접 정의한 에러는 `detail`에 `code`와 `message`를 담습니다. 채팅 실패 응답은 대화를 이어갈 수 있도록 `session_id`를 함께 반환합니다.

```json
{
    "detail": {
        "code": "USERNAME_TAKEN",
        "message": "이미 사용 중인 아이디입니다."
    }
}
```

| 상태 | code | 상황 |
|---|---|---|
| 400 | `MODEL_UNAVAILABLE` | 없는 모델이나 비활성 모델로 질문 |
| 400 | `SELF_MODIFY` | 관리자가 자기 계정을 비활성화하거나 권한을 낮춤 |
| 400 | `DEFAULT_MODEL_REQUIRED` | 기본 모델을 비활성화하거나 기본 지정을 해제함 |
| 400 | `CODE_EXPIRED` | 인증 코드 유효 시간(10분) 경과 |
| 400 | `INVALID_CODE` | 인증 코드 불일치, 인증 대상 없음 |
| 400 | `TOO_MANY_ATTEMPTS` | 인증 코드를 5회 틀린 뒤 다시 확인 요청 |
| 401 | `UNAUTHORIZED` | 로그인 쿠키가 없거나 유효하지 않음 |
| 401 | `INVALID_CREDENTIALS` | 아이디 또는 비밀번호 불일치 |
| 403 | `USER_DISABLED` | 비활성화된 계정 |
| 403 | `EMAIL_NOT_VERIFIED` | 이메일 인증 전 로그인 |
| 403 | `FORBIDDEN` | 관리자 API에 일반 사용자가 접근 |
| 404 | `NOT_FOUND` | 없거나 본인 것이 아닌 대화, 없는 모델 |
| 409 | `USERNAME_TAKEN` | 이미 사용 중인 아이디로 가입 |
| 409 | `EMAIL_TAKEN` | 이미 사용 중인 이메일로 가입 |
| 409 | `DEFAULT_MODEL_CONFLICT` | 여러 관리자가 동시에 기본 모델을 변경 |
| 429 | `QUOTA_EXCEEDED` | 이번 달 토큰 사용량이 한도 이상 |
| 429 | `TOO_MANY_REQUESTS` | 같은 아이디나 이메일로 60초 안에 인증 코드 재발송 요청 |
| 500 | `DB_ERROR` | 메시지 저장 실패(응답에 `session_id` 포함) |
| 502 | `AI_ERROR` | AI API 오류 응답, 연결 실패, 빈 응답 |
| 504 | `AI_TIMEOUT` | AI API 응답이 `AI_TIMEOUT_SECONDS` 안에 오지 않음 |

입력 형식 오류는 FastAPI 기본 형식의 422로 응답합니다. 공백만 입력한 질문은 앞뒤 공백을 제거한 뒤 검사하므로 422가 됩니다.

```
POST /api/chat {"message":"   "}
HTTP 422
{
    "detail": [
        {
            "type": "string_too_short",
            "loc": [
                "body",
                "message"
            ],
            "msg": "String should have at least 1 character",
            "input": "   ",
            "ctx": {
                "min_length": 1
            }
        }
    ]
}
```

## 인증

회원가입 필드는 `username`(영문 소문자, 숫자, 밑줄 3~30자), `password`(8~72자, 72바이트 이하), `name`(앞뒤 공백 제거 후 1~30자), `email`입니다. 이메일은 소문자로 저장됩니다. 가입하면 6자리 인증 코드를 이메일로 발송하고, 인증 전에는 `email_verified_at`이 `null`입니다.

```
POST /api/auth/signup {"username":"alice","password":"password1","name":"앨리스","email":"alice@example.com"}
HTTP 201
{
    "id": 2,
    "username": "alice",
    "name": "앨리스",
    "email": "alice@example.com",
    "email_verified_at": null,
    "role": "user",
    "is_active": true,
    "token_limit": 100000,
    "created_at": "2026-10-07T09:07:48.700329Z"
}
```

```
POST /api/auth/signup {"username":"bob","password":"password1","name":"밥","email":"alice@example.com"}
HTTP 409
{
    "detail": {
        "code": "EMAIL_TAKEN",
        "message": "이미 사용 중인 이메일입니다."
    }
}
```

이메일 인증 전에는 로그인할 수 없습니다.

```
POST /api/auth/login {"username":"alice","password":"password1"}
HTTP 403
{
    "detail": {
        "code": "EMAIL_NOT_VERIFIED",
        "message": "이메일 인증이 필요합니다."
    }
}
```

`/api/auth/verify-email`은 `username`이나 `email` 중 하나와 `code`를 받습니다. 코드는 10분 동안 유효합니다.

```
POST /api/auth/verify-email {"username":"alice","code":"000000"}
HTTP 400
{
    "detail": {
        "code": "INVALID_CODE",
        "message": "인증 코드가 올바르지 않습니다."
    }
}
```

5회 틀린 뒤에는 올바른 코드를 보내도 `TOO_MANY_ATTEMPTS`로 응답하며, 코드를 다시 요청해야 합니다.

```
POST /api/auth/verify-email {"username":"alice","code":"482913"}
HTTP 400
{
    "detail": {
        "code": "TOO_MANY_ATTEMPTS",
        "message": "인증 시도 횟수를 초과했습니다. 코드를 다시 요청해 주세요."
    }
}
```

```
POST /api/auth/verify-email {"username":"alice","code":"482913"}
HTTP 400
{
    "detail": {
        "code": "CODE_EXPIRED",
        "message": "인증 코드가 만료되었습니다."
    }
}
```

```
POST /api/auth/verify-email {"email":"alice@example.com","code":"482913"}
HTTP 200
{
    "id": 2,
    "username": "alice",
    "name": "앨리스",
    "email": "alice@example.com",
    "email_verified_at": "2026-10-07T09:07:49.620976Z",
    "role": "user",
    "is_active": true,
    "token_limit": 100000,
    "created_at": "2026-10-07T09:07:48.700329Z"
}
```

`/api/auth/resend-code`는 `username`이나 `email`을 받아 새 코드를 발송하고 204를 반환합니다. 가입되지 않았거나 이미 인증한 계정이어도 같은 204를 반환해 계정 존재 여부를 노출하지 않습니다. 같은 아이디나 이메일로 60초 안에 다시 요청하면 429입니다. 가입 직후나 직전 코드 발급 후 60초 안의 첫 재발송 요청은 204를 반환하지만 새 코드는 발송하지 않으며, 이미 발송한 코드를 그대로 사용합니다.

```
POST /api/auth/resend-code {"username":"alice"}
HTTP 204
```

```
POST /api/auth/resend-code {"username":"alice"}
HTTP 429
{
    "detail": {
        "code": "TOO_MANY_REQUESTS",
        "message": "잠시 후 다시 요청해 주세요."
    }
}
```

아이디나 비밀번호가 틀리면 401을 반환합니다.

```
POST /api/auth/login {"username":"alice","password":"wrongpass"}
HTTP 401
{
    "detail": {
        "code": "INVALID_CREDENTIALS",
        "message": "아이디 또는 비밀번호가 올바르지 않습니다."
    }
}
```

로그인에 성공하면 본문은 회원가입 응답과 같은 형식의 사용자 정보이고, 헤더로 쿠키가 발급됩니다. 토큰 값은 `<JWT>`로 가렸습니다.

```
POST /api/auth/login {"username":"alice","password":"password1"}
HTTP/1.1 200 OK
set-cookie: access_token=<JWT>; HttpOnly; Max-Age=86400; Path=/; SameSite=lax
```

로그아웃은 쿠키를 삭제하고 204를 반환합니다. 이후 `/api/auth/me`는 401입니다.

```
POST /api/auth/logout
HTTP 204

GET /api/auth/me
HTTP 401
{
    "detail": {
        "code": "UNAUTHORIZED",
        "message": "로그인이 필요합니다."
    }
}
```

## 모델과 프리셋

`/api/models`는 활성 모델만 `sort_order` 순서로 반환합니다. `multiplier`는 토큰 과금 배율이고 `is_default`인 모델이 질문에 모델을 지정하지 않았을 때 사용됩니다.

```
GET /api/models
HTTP 200
[
    {
        "code": "gemini-3-flash",
        "name": "Gemini 3 Flash",
        "provider": "google",
        "multiplier": 0.5,
        "is_default": false
    },
    {
        "code": "gemini-3.1-flash-lite",
        "name": "Gemini 3.1 Flash Lite",
        "provider": "google",
        "multiplier": 0.5,
        "is_default": false
    },
    ...
]
```

```
GET /api/presets
HTTP 200
[
    {
        "code": "tutor",
        "name": "학습 튜터",
        "description": "개념을 단계별로 설명하고 이해를 확인합니다."
    },
    {
        "code": "code_review",
        "name": "코드 리뷰어",
        "description": "코드의 문제점과 개선 방향을 짚어 줍니다."
    },
    {
        "code": "debug",
        "name": "디버깅 도우미",
        "description": "오류 메시지와 증상으로 원인을 함께 찾습니다."
    },
    {
        "code": "concept",
        "name": "개념 설명",
        "description": "용어와 개념을 짧고 정확하게 설명합니다."
    }
]
```

## 대화

대화 생성 시 제목과 모델을 생략하면 `새 대화`와 기본 모델이 사용됩니다. 목록은 `updated_at` 최신순입니다.

```
POST /api/sessions {"title":"파이썬 질문"}
HTTP 201
{
    "id": 1,
    "title": "파이썬 질문",
    "model_code": "gpt-5-mini",
    "preset": "tutor",
    "created_at": "2026-10-07T08:03:14.131601Z",
    "updated_at": "2026-10-07T08:03:14.131601Z",
    "message_count": 0
}
```

```
PATCH /api/sessions/1 {"title":"파이썬 리스트 질문","preset":"concept"}
HTTP 200
{
    "id": 1,
    "title": "파이썬 리스트 질문",
    "model_code": "gpt-5-mini",
    "preset": "concept",
    "created_at": "2026-10-07T08:03:14.131601Z",
    "updated_at": "2026-10-07T08:03:14.234218Z",
    "message_count": 0
}
```

다른 사용자의 대화나 삭제된 대화는 404입니다. 아래는 새로 만든 대화를 삭제한 예시입니다.

```
POST /api/sessions {"title":"삭제할 대화"}
HTTP 201
{
    "id": 2,
    "title": "삭제할 대화",
    "model_code": "gpt-5-mini",
    "preset": "tutor",
    "created_at": "2026-10-07T09:12:02.626675Z",
    "updated_at": "2026-10-07T09:12:02.626675Z",
    "message_count": 0
}
```

```
DELETE /api/sessions/2
HTTP 204

GET /api/sessions/2/messages
HTTP 404
{
    "detail": {
        "code": "NOT_FOUND",
        "message": "대화를 찾을 수 없습니다."
    }
}
```

## 채팅

요청 필드는 `message`(앞뒤 공백 제거 후 1~4000자)와 선택 필드 `session_id`, `model_code`, `preset`입니다. `session_id`가 없으면 질문 앞 30자를 제목으로 대화를 새로 만듭니다. AI에는 프리셋 시스템 프롬프트와 같은 대화에서 정상 처리된 최근 `CONTEXT_WINDOW`개 메시지를 전달합니다.

```
POST /api/chat {"message":"파이썬 리스트와 튜플 차이를 한 문장으로 알려줘"}
HTTP 200
{
    "session_id": 2,
    "user_message": {
        "id": 3,
        "session_id": 2,
        "role": "user",
        "content": "파이썬 리스트와 튜플 차이를 한 문장으로 알려줘",
        "status": "ok",
        "error_code": null,
        "model_code": null,
        "input_tokens": 0,
        "output_tokens": 0,
        "billed_tokens": 0,
        "latency_ms": null,
        "created_at": "2026-10-07T08:40:46.100943Z"
    },
    "assistant_message": {
        "id": 4,
        "session_id": 2,
        "role": "assistant",
        "content": "리스트는 대괄호로 만들고 내부 값을 언제든 변경할 수 있는(mutable) 시퀀스인 반면, 튜플은 소괄호로 만들고 생성 후 값을 바꿀 수 없는(immutable) 시퀀스입니다.\n\n간단히 풀어 설명하면:\n- 리스트: a = [1, 2]; a[0] = 9  # 가능, a.append(3) 등\n- 튜플: t = (1, 2); t[0] = 9  # 불가능, TypeError 발생  \n- 사용처: 리스트는 요소를 자주 추가·수정할 때, 튜플은 변경되지 않는 고정된 데이터(예: 딕셔너리의 키나 레코드)를 쓸 때 적합합니다.",
        "status": "ok",
        "error_code": null,
        "model_code": "gpt-5-mini",
        "input_tokens": 81,
        "output_tokens": 630,
        "billed_tokens": 356,
        "latency_ms": 6581,
        "created_at": "2026-10-07T08:40:52.697394Z"
    },
    "usage": {
        "month_used": 654,
        "token_limit": 100000,
        "remaining": 99346
    }
}
```

`billed_tokens`는 `ceil((81 + 630) x 0.5) = 356`이고, `usage`는 이 답변까지 포함한 이번 달 사용량입니다.

AI 호출이 실패하면 질문과 안내 문구를 `status: error`로 저장한 뒤 502 또는 504를 반환합니다.

```
POST /api/chat {"session_id":1,"message":"리스트와 튜플의 차이를 알려 주세요"}
HTTP 502
{
    "detail": {
        "code": "AI_ERROR",
        "message": "AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.",
        "session_id": 1
    }
}
```

```
POST /api/chat {"session_id":1,"message":"timeout 긴 글 요약해줘"}
HTTP 504
{
    "detail": {
        "code": "AI_TIMEOUT",
        "message": "현재 응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.",
        "session_id": 1
    }
}
```

두 요청 뒤 메시지 목록입니다. 실패한 질문과 답변은 기록에 남고 다음 질문의 문맥에서는 제외됩니다.

```
GET /api/sessions/1/messages
HTTP 200
[
    {
        "id": 1,
        "session_id": 1,
        "role": "user",
        "content": "리스트와 튜플의 차이를 알려 주세요",
        "status": "error",
        "error_code": "AI_ERROR",
        "model_code": null,
        "input_tokens": 0,
        "output_tokens": 0,
        "billed_tokens": 0,
        "latency_ms": null,
        "created_at": "2026-10-07T08:03:14.332727Z"
    },
    {
        "id": 2,
        "session_id": 1,
        "role": "assistant",
        "content": "AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.",
        "status": "error",
        "error_code": "AI_ERROR",
        "model_code": "gpt-5-mini",
        "input_tokens": 0,
        "output_tokens": 0,
        "billed_tokens": 0,
        "latency_ms": 235,
        "created_at": "2026-10-07T08:03:14.343000Z"
    },
    {
        "id": 3,
        "session_id": 1,
        "role": "user",
        "content": "timeout 긴 글 요약해줘",
        "status": "error",
        "error_code": "AI_TIMEOUT",
        "model_code": null,
        "input_tokens": 0,
        "output_tokens": 0,
        "billed_tokens": 0,
        "latency_ms": null,
        "created_at": "2026-10-07T08:03:14.644619Z"
    },
    {
        "id": 4,
        "session_id": 1,
        "role": "assistant",
        "content": "현재 응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.",
        "status": "error",
        "error_code": "AI_TIMEOUT",
        "model_code": "gpt-5-mini",
        "input_tokens": 0,
        "output_tokens": 0,
        "billed_tokens": 0,
        "latency_ms": 2001,
        "created_at": "2026-10-07T08:03:14.651627Z"
    }
]
```

같은 두 요청의 서버 로그입니다. `request_id`로 요청 수신부터 AI 호출 실패, DB 저장까지 연결됩니다.

```
2026-10-07 17:03:14,335 INFO request_received user_id=2 path=/api/chat request_id=9b292d24d235
2026-10-07 17:03:14,344 INFO db_save_success user_id=2 message_id=1
2026-10-07 17:03:14,583 WARNING ai_call_fail request_id=9b292d24d235 error_code=AI_ERROR latency_ms=235
2026-10-07 17:03:14,591 INFO db_save_success user_id=2 message_id=2
2026-10-07 17:03:14,646 INFO request_received user_id=2 path=/api/chat request_id=87c5edf00c71
2026-10-07 17:03:14,653 INFO db_save_success user_id=2 message_id=3
2026-10-07 17:03:16,657 WARNING ai_call_fail request_id=87c5edf00c71 error_code=AI_TIMEOUT latency_ms=2001
2026-10-07 17:03:16,662 INFO db_save_success user_id=2 message_id=4
```

없는 모델을 지정하면 대화를 만들기 전에 400을 반환합니다.

```
POST /api/chat {"message":"안녕","model_code":"unknown"}
HTTP 400
{
    "detail": {
        "code": "MODEL_UNAVAILABLE",
        "message": "사용할 수 없는 모델입니다."
    }
}
```

이번 달(KST 1일 0시 이후) 사용량이 한도 이상이면 질문을 저장하지 않고 429를 반환합니다. 아래는 관리자가 한도를 0으로 바꾼 뒤의 요청입니다.

```
POST /api/chat {"message":"안녕"}
HTTP 429
{"detail":{"code":"QUOTA_EXCEEDED","message":"이번 달 사용량을 모두 사용했습니다. 관리자에게 문의해 주세요."}}
```

## 내 기록과 사용량

`/api/me/chats`는 질문 하나와 그에 대한 답변을 한 항목으로 묶어 최신순으로 반환합니다. `limit`(1~100, 기본 50)과 `offset`으로 페이지를 나눕니다.

```
GET /api/me/chats?limit=2
HTTP 200
{
    "items": [
        {
            "id": 3,
            "session_id": 1,
            "session_title": "파이썬 리스트 질문",
            "question": "timeout 긴 글 요약해줘",
            "answer": "현재 응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.",
            "status": "error",
            "error_code": "AI_TIMEOUT",
            "model_code": "gpt-5-mini",
            "billed_tokens": 0,
            "created_at": "2026-10-07T08:03:14.644619Z"
        },
        {
            "id": 1,
            "session_id": 1,
            "session_title": "파이썬 리스트 질문",
            "question": "리스트와 튜플의 차이를 알려 주세요",
            "answer": "AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.",
            "status": "error",
            "error_code": "AI_ERROR",
            "model_code": "gpt-5-mini",
            "billed_tokens": 0,
            "created_at": "2026-10-07T08:03:14.332727Z"
        }
    ],
    "total": 2
}
```

`billed_tokens`는 `ceil((입력 토큰 + 출력 토큰) x 모델 배율)`이며, 실패한 요청은 0입니다.

```
GET /api/me/usage
HTTP 200
{
    "month_used": 0,
    "token_limit": 100000,
    "remaining": 100000
}
```

## 관리자

`ADMIN_USERNAME`과 `ADMIN_PASSWORD`가 설정되어 있으면 서버 시작 시 관리자 계정이 생성됩니다. 이 계정은 이메일 없이 인증 완료 상태로 생성됩니다. 일반 사용자가 관리자 API에 접근하면 403입니다.

```
GET /api/admin/users
HTTP 403
{
    "detail": {
        "code": "FORBIDDEN",
        "message": "관리자만 사용할 수 있습니다."
    }
}
```

```
GET /api/admin/users
HTTP 200
[
    {
        "id": 1,
        "username": "admin",
        "name": "admin",
        "email": null,
        "email_verified_at": "2026-10-07T09:07:42.254750Z",
        "role": "admin",
        "is_active": true,
        "token_limit": 100000,
        "created_at": "2026-10-07T09:07:42.085745Z",
        "month_used": 0,
        "session_count": 0
    },
    {
        "id": 2,
        "username": "alice",
        "name": "앨리스",
        "email": "alice@example.com",
        "email_verified_at": "2026-10-07T09:07:49.620976Z",
        "role": "user",
        "is_active": true,
        "token_limit": 100000,
        "created_at": "2026-10-07T09:07:48.700329Z",
        "month_used": 0,
        "session_count": 1
    }
]
```

```
PATCH /api/admin/users/2 {"token_limit":50000}
HTTP 200
{
    "id": 2,
    "username": "alice",
    "name": "앨리스",
    "email": "alice@example.com",
    "email_verified_at": "2026-10-07T09:07:49.620976Z",
    "role": "user",
    "is_active": true,
    "token_limit": 50000,
    "created_at": "2026-10-07T09:07:48.700329Z",
    "month_used": 0,
    "session_count": 1
}
```

```
PATCH /api/admin/users/1 {"role":"user"}
HTTP 400
{
    "detail": {
        "code": "SELF_MODIFY",
        "message": "자기 계정은 비활성화하거나 권한을 낮출 수 없습니다."
    }
}
```

`/api/admin/chats`는 `/api/me/chats`와 같은 형식에 `username`과 `name`을 더해 반환하며, `user_id`를 지정하면 해당 사용자의 기록만 조회합니다.

```
GET /api/admin/chats?user_id=2&limit=1
HTTP 200
{
    "items": [
        {
            "id": 1,
            "session_id": 1,
            "session_title": "리스트와 튜플의 차이를 알려 주세요",
            "question": "리스트와 튜플의 차이를 알려 주세요",
            "answer": "AI 응답을 받지 못했어요. 잠시 후 다시 시도해 주세요.",
            "status": "error",
            "error_code": "AI_ERROR",
            "model_code": "gpt-5-mini",
            "billed_tokens": 0,
            "created_at": "2026-10-07T09:07:49.912091Z",
            "username": "alice",
            "name": "앨리스"
        }
    ],
    "total": 1
}
```

`/api/admin/models`는 비활성 모델을 포함한 전체 목록을 반환합니다. 변경 가능한 필드는 `is_active`, `is_default`, `multiplier`(0 초과 99.99 이하), `max_tokens`(1~32000), `sort_order`입니다. 다른 모델을 기본으로 지정하면 기존 기본 모델은 해제됩니다.

```
GET /api/admin/models
HTTP 200
[
    {
        "code": "gemini-3-flash",
        "name": "Gemini 3 Flash",
        "provider": "google",
        "multiplier": 0.5,
        "is_default": false,
        "max_tokens": 4096,
        "is_active": true,
        "sort_order": 0
    },
    ...
]
```

```
PATCH /api/admin/models/gpt-5.4 {"is_default":true}
HTTP 200
{
    "code": "gpt-5.4",
    "name": "GPT-5.4",
    "provider": "openai",
    "multiplier": 1.0,
    "is_default": true,
    "max_tokens": 4096,
    "is_active": true,
    "sort_order": 9
}
```

```
PATCH /api/admin/models/gpt-5.4 {"is_active":false}
HTTP 400
{
    "detail": {
        "code": "DEFAULT_MODEL_REQUIRED",
        "message": "기본 모델은 비활성화할 수 없습니다."
    }
}
```

`/api/admin/usage`는 최근 `days`일(1~365, 기본 30)의 정상 답변을 KST 날짜와 모델별로 집계해 `[{date, model_code, billed_tokens, requests}]` 형식으로 반환합니다.

```
GET /api/admin/usage?days=7
HTTP 200
[
    {
        "date": "2026-10-07",
        "model_code": "gpt-5-mini",
        "billed_tokens": 654,
        "requests": 2
    }
]
```
