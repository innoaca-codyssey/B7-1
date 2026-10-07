# B7-1 웹 기반 AI 챗봇 서비스

사용자 문의에 실시간으로 응답하는 AI 챗봇 서비스입니다. 로그인한 사용자가 웹 화면에서 질문하면 서버가 AI API를 호출해 응답을 생성하고, 같은 화면에 답변을 표시합니다. 질문과 답변은 PostgreSQL에 사용자별로 누적 저장되며, 같은 대화의 최근 메시지를 함께 보내 이전 질문을 이어서 물어볼 수 있습니다.

서비스 주소: https://chat.codyssey.run

API 문서: https://chat.codyssey.run/api/docs (Swagger UI), https://chat.codyssey.run/api/redoc (ReDoc)

## 프로젝트 개요

- 문제 정의: 프로그래밍을 공부하다 생긴 질문을 바로 물어볼 곳이 필요하고, 물어본 내용을 나중에 다시 찾아볼 수 있어야 합니다.
- 타겟 사용자: 프로그래밍을 공부하는 학습자
- 핵심 시나리오: 회원가입, 이메일 인증, 로그인, 새 대화 시작, 모델과 프리셋 선택, 질문 입력, 답변 확인, 이전 대화 이어서 질문, 내 대화 기록 조회

## 기술 스택

| 구분 | 사용 |
|---|---|
| 프론트엔드 | React, TypeScript, Vite |
| 백엔드 | Python, FastAPI, SQLAlchemy |
| DB | PostgreSQL |
| AI | Codyssey Public API (OpenAI 호환) |
| 실행 | Docker Compose, Nginx |

## 화면

### 로그인과 회원가입

![로그인](docs/images/login.png)

![회원가입](docs/images/signup.png)

회원가입 후 입력한 이메일로 6자리 인증 코드가 발송됩니다. 인증을 마치기 전에는 로그인할 수 없습니다.

![이메일 인증](docs/images/verify-email.png)

### 채팅

![채팅](docs/images/chat-view.png)

왼쪽은 대화 목록, 오른쪽은 선택한 대화의 메시지입니다. 입력창 위에서 모델과 프리셋(학습 튜터, 코드 리뷰어, 디버깅 도우미, 개념 설명)을 선택합니다. 답변은 마크다운으로 표시되고, 메시지마다 과금 토큰 수가 표시됩니다.

![대화 목록](docs/images/session-sidebar.png)

AI 호출이 실패하거나 시간이 초과되면 오류 코드와 안내 문구가 대화에 함께 남습니다.

![오류 안내](docs/images/chat-error.png)

좁은 화면에서는 대화 목록이 상단의 대화 목록 버튼으로 여는 패널로 바뀝니다.

![좁은 화면 대화](docs/images/mobile-chat.png)

![좁은 화면 대화 목록](docs/images/mobile-sidebar.png)

### 내 대화 기록

![내 대화 기록](docs/images/my-logs.png)

### 관리자

![관리자 사용자](docs/images/admin-users.png)

![관리자 모델](docs/images/admin-models.png)

![관리자 사용량](docs/images/admin-usage.png)

관리자는 사용자의 역할, 활성 상태, 월 토큰 한도를 변경하고, 모델의 활성 여부와 기본 모델, 토큰 배율을 설정합니다. 일별 모델 사용량과 전체 사용자의 대화 로그도 조회할 수 있습니다.

## 시스템 구조

```mermaid
flowchart LR
    B[브라우저] -->|"/"| W[web: Nginx + React 빌드]
    W -->|"/api"| A[api: FastAPI]
    A --> D[(db: PostgreSQL)]
    A -->|HTTPS| C[Codyssey Public API]
    A -->|SMTP| M[Amazon SES]
```

브라우저는 `web` 컨테이너 하나에만 접속합니다. Nginx가 React 빌드 결과를 제공하고 `/api`로 시작하는 요청을 `api` 컨테이너로 전달하므로, 프론트엔드와 API가 같은 오리진을 사용합니다. 그래서 로그인 토큰을 httpOnly 쿠키로 주고받을 수 있고 CORS 설정이 필요하지 않습니다. AI API 키와 SMTP 자격 증명은 `api` 컨테이너의 환경 변수에만 있으며 브라우저로 전달되지 않습니다.

### 주요 컴포넌트 역할

| 위치 | 역할 |
|---|---|
| `frontend/` | 로그인, 회원가입, 채팅, 내 대화 기록, 관리자 화면 |
| `backend/app/routers/` | URL과 요청/응답 스키마를 연결합니다. 쿼리는 직접 작성하지 않고 `crud`와 `services`를 호출합니다 |
| `backend/app/schemas/` | Pydantic 요청/응답 모델. 입력 길이와 형식 검증을 담당합니다 |
| `backend/app/crud/` | DB 조회와 저장 함수 |
| `backend/app/services/` | AI API 호출, 채팅 처리, 사용량 계산, 이메일 인증 코드 발송 |
| `backend/app/deps.py` | 쿠키의 JWT로 현재 사용자를 확인하고, 관리자 권한을 검사합니다 |
| `backend/app/security.py` | bcrypt 비밀번호 해시, JWT 발급과 검증 |
| `backend/app/models.py` | SQLAlchemy 테이블 정의. 앱 시작 시 테이블을 생성합니다 |

## DB 구조

```mermaid
erDiagram
    users ||--o{ chat_sessions : "소유"
    users ||--o{ messages : "작성"
    users ||--o{ email_verifications : "인증"
    chat_sessions ||--o{ messages : "포함"

    users {
        int id PK
        varchar(30) username UK
        varchar(30) display_name
        varchar(254) email UK
        timestamptz email_verified_at
        varchar(255) password_hash
        varchar(10) role "user, admin"
        bool is_active
        int token_limit "월 토큰 한도"
        timestamptz created_at
    }
    email_verifications {
        int id PK
        int user_id FK
        varchar(64) code_hash "sha256"
        timestamptz expires_at
        int attempts
        timestamptz created_at
    }
    chat_sessions {
        int id PK
        int user_id FK
        varchar(100) title
        varchar(50) model_code
        varchar(20) preset
        timestamptz created_at
        timestamptz updated_at
    }
    messages {
        int id PK
        int session_id FK
        int user_id FK
        varchar(10) role "user, assistant"
        text content
        varchar(10) status "ok, error"
        varchar(30) error_code
        varchar(50) model_code
        int input_tokens
        int output_tokens
        int billed_tokens
        int latency_ms
        varchar(32) request_id
        timestamptz created_at
    }
    ai_models {
        int id PK
        varchar(50) code UK
        varchar(50) name
        varchar(20) provider
        numeric multiplier "토큰 배율"
        int max_tokens
        bool is_active
        bool is_default
        int sort_order
    }
```

- 질문과 답변은 `messages`에 한 행씩 저장합니다. 질문 행은 `role=user`, 바로 다음 답변 행은 `role=assistant`입니다.
- `messages.user_id`는 `chat_sessions`를 거치지 않고 사용자 기준으로 바로 조회하기 위해 둡니다. `(user_id, created_at)`, `(session_id, created_at)` 인덱스가 있습니다.
- 사용자나 대화를 삭제하면 하위 대화와 메시지가 외래 키의 `ON DELETE CASCADE`로 함께 삭제됩니다.
- `ai_models`는 선택 가능한 모델 목록입니다. `chat_sessions.model_code`와 `messages.model_code`는 `ai_models.code` 값을 저장하지만 외래 키는 두지 않았습니다. 관리자가 모델을 비활성화해도 지난 대화 기록은 그대로 남아야 하기 때문입니다.
- 이메일 인증 코드는 원문 대신 sha256 해시로 저장합니다. 코드는 10분 동안 유효하고, 5회 틀리면 무효가 됩니다. 재발송하면 이전 코드는 삭제됩니다.
- 이미 운영 중인 DB에는 API 시작 시 `display_name`, `email`, `email_verified_at` 컬럼을 추가합니다. 기존 사용자는 이메일 인증을 마친 상태로 처리하며, 컬럼이 이미 있으면 테이블을 변경하지 않습니다.

## API

요청과 응답 예시는 [docs/api.md](docs/api.md)에, 요청과 응답 스키마는 Swagger UI(https://chat.codyssey.run/api/docs)와 ReDoc(https://chat.codyssey.run/api/redoc)에 있습니다. Swagger UI에서 `POST /api/auth/login`을 실행하면 이후 요청을 로그인 상태로 시험할 수 있습니다. 모든 API는 `/api`로 시작하며, 로그인이 필요한 API는 `access_token` 쿠키로 사용자를 확인합니다.

| 메서드 | 경로 | 설명 | 권한 |
|---|---|---|---|
| POST | `/api/auth/signup` | 회원가입, 인증 코드 발송 | |
| POST | `/api/auth/verify-email` | 이메일 인증 코드 확인 | |
| POST | `/api/auth/resend-code` | 인증 코드 재발송 | |
| POST | `/api/auth/login` | 로그인, 쿠키 발급 | |
| POST | `/api/auth/logout` | 로그아웃, 쿠키 삭제 | |
| GET | `/api/auth/me` | 내 정보 | 로그인 |
| GET, POST | `/api/sessions` | 대화 목록, 새 대화 | 로그인 |
| PATCH, DELETE | `/api/sessions/{session_id}` | 대화 제목, 모델, 프리셋 변경과 삭제 | 로그인 |
| GET | `/api/sessions/{session_id}/messages` | 대화의 메시지 목록 | 로그인 |
| GET | `/api/models` | 사용 가능한 모델 목록 | |
| GET | `/api/presets` | 프리셋 목록 | |
| POST | `/api/chat` | 질문 전송, AI 답변 | 로그인 |
| GET | `/api/me/usage` | 이번 달 토큰 사용량 | 로그인 |
| GET | `/api/me/chats` | 내 대화 기록 | 로그인 |
| GET, PATCH | `/api/admin/users`, `/api/admin/users/{user_id}` | 사용자 목록, 역할, 상태, 한도 변경 | 관리자 |
| GET | `/api/admin/chats` | 전체 사용자 대화 로그 | 관리자 |
| GET, PATCH | `/api/admin/models`, `/api/admin/models/{code}` | 모델 목록, 활성 여부, 기본 모델, 배율 변경 | 관리자 |
| GET | `/api/admin/usage` | 일별 모델 사용량 | 관리자 |

## 대화 로그 저장과 조회

질문과 답변을 DB에 저장하는 이유는 세 가지입니다.

- 문맥 유지: 같은 대화에서 `status=ok`인 최근 `CONTEXT_WINDOW`개 메시지(방금 보낸 질문 포함)를 DB에서 읽어 프리셋의 시스템 프롬프트와 함께 AI에 보냅니다. AI 호출이 실패한 질문과 오류 안내 메시지는 `status=error`로 저장되므로 문맥에서 제외됩니다. 서버 메모리에 대화를 들고 있지 않으므로 API를 다시 시작해도 대화를 이어갈 수 있습니다.
- 사용자 기준 추적: 모든 메시지에 `user_id`와 `created_at`이 있어 사용자별, 기간별로 조회할 수 있습니다. AI 호출이 실패한 경우에도 질문과 `status=error`, `error_code`가 남으므로 어떤 요청이 왜 실패했는지 확인할 수 있습니다.
- 사용량 제한: 이번 달(KST 기준) `billed_tokens` 합계를 `users.token_limit`과 비교해 한도를 넘으면 요청을 차단합니다.

### SQL로 확인하기

`scripts/check_logs.sql`에는 사용자별 최근 대화 5건과, 사용자별 질문 수, 오류 수, 토큰 합계를 조회하는 쿼리가 있습니다. 답변이 저장되지 않은 질문은 `status`가 `error`로 표시됩니다.

```bash
docker compose exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < scripts/check_logs.sql
```

로컬 실행 예시입니다. 관리자 계정으로 질문 3개를 보낸 뒤 실행했습니다. 세 번째 질문 "방금 내가 뭘 물어봤지?"는 첫 질문과 같은 대화에서 보냈고, 이전 질문을 문맥으로 받아 답했습니다.

```
 username |                 session_title                  |                    question                    |                                                                                 answer                                                                                 | status | error_code |          created_at           
----------+------------------------------------------------+------------------------------------------------+------------------------------------------------------------------------------------------------------------------------------------------------------------------------+--------+------------+-------------------------------
 admin    | 파이썬 리스트와 튜플 차이를 한 문장으로 알려줘 | 방금 내가 뭘 물어봤지?                         | 방금 "파이썬 리스트와 튜플 차이를 한 문장으로 알려줘"라고 물어보셨어요.                                                                                                | ok     |            | 2026-10-07 09:13:21.057407+00
 admin    | SQL JOIN 종류를 한 줄씩 설명해줘               | SQL JOIN 종류를 한 줄씩 설명해줘               | 먼저 간단히: JOIN은 둘 이상의 테이블을 특정 조건으로 연결해 관련된 행들을 함께 조회하는 연산이야.                                                                     +| ok     |            | 2026-10-07 09:13:12.272897+00
          |                                                |                                                |                                                                                                                                                                       +|        |            | 
          |                                                |                                                | - INNER JOIN: 양쪽 테이블에서 조건에 맞는 행들만 교집합처럼 반환한다.                                                                                                 +|        |            | 
          |                                                |                                                | - LEFT (LEFT OUTER) JOIN: 왼쪽 테이블의 모든 행과, 조건에 맞는 오른쪽 행을 매칭하고 없으면 NULL로 채운다.                                                             +|        |            | 
          |                                                |                                                | - RIGHT (RIGHT OUTER) JOIN: 오른쪽 테이블의 모든 행과, 조건에 맞는 왼쪽 행을 매칭하고 없으면 NULL로 채운다.                                                           +|        |            | 
          |                                                |                                                | - FULL (FULL OUTER) JOIN: 양쪽 테이블의 모든 행을 포함하되, 조건에 맞으면 합치고 아니면 상대편 컬럼을 NULL로 채운다.                                                  +|        |            | 
          |                                                |                                                | - CROSS JOIN: 조건 없이 두 테이블의 모든 조합(카티션 곱)을 생성한다.                                                                                                  +|        |            | 
          |                                                |                                                | - SELF JOIN: 같은 테이블을 서로 다른 별칭으로 사용해 한 테이블의 행들끼리 비교하거나 연결할 때 쓴다.                                                                  +|        |            | 
          |                                                |                                                | - NATURAL JOIN: 동일한 이름의 컬럼들을 자동으로 기준으로 하여 매칭하는 JOIN(주의: 예상치 못한 컬럼 매칭 위험 있음).                                                   +|        |            | 
          |                                                |                                                | - SEMI JOIN (구현적 개념): 왼쪽 테이블의 행 중 오른쪽 테이블에 매칭이 존재하는 행만 반환(예: WHERE EXISTS) — 일부 DB엔 키워드로 없음.                                 +|        |            | 
          |                                                |                                                | - ANTI JOIN (구현적 개념): 왼쪽 테이블의 행 중 오른쪽 테이블에 매칭이 없는 행만 반환(예: WHERE NOT EXISTS) — 일부 DB엔 키워드로 없음.                                 +|        |            | 
          |                                                |                                                |                                                                                                                                                                       +|        |            | 
          |                                                |                                                | 원하면 각 JOIN별로 짧은 SQL 예제와 시각적인 행 매칭 그림도 보여줄게. 어느 JOIN부터 예제를 보고 싶어?                                                                   |        |            | 
 admin    | 파이썬 리스트와 튜플 차이를 한 문장으로 알려줘 | 파이썬 리스트와 튜플 차이를 한 문장으로 알려줘 | 리스트는 대괄호로 만들고 요소를 변경할 수 있는(mutable) 순서 있는 컬렉션인 반면, 튜플은 소괄호로 만들고 생성 후 요소를 바꿀 수 없는(immutable) 순서 있는 컬렉션입니다.+| ok     |            | 2026-10-07 09:13:06.452356+00
          |                                                |                                                |                                                                                                                                                                       +|        |            | 
          |                                                |                                                | 간단히 정리하면:                                                                                                                                                      +|        |            | 
          |                                                |                                                | - 리스트: [] 사용, a = [1,2,3]; a[0] = 10  # 가능                                                                                                                     +|        |            | 
          |                                                |                                                | - 튜플: () 사용, b = (1,2,3); b[0] = 10  # TypeError 발생                                                                                                              |        |            | 
(3 rows)

 username | questions | errors | tokens | billed_tokens 
----------+-----------+--------+--------+---------------
 admin    |         3 |      0 |   2044 |          1022
(1 row)
```

### API로 확인하기

로그인하면 받은 `access_token` 쿠키로 내 대화 기록을 조회합니다. `limit`(1~100, 기본 50)과 `offset`으로 페이지를 나눕니다.

```bash
curl -s -c cookies.txt -H 'Content-Type: application/json' \
  -d '{"username":"<아이디>","password":"<비밀번호>"}' https://chat.codyssey.run/api/auth/login
curl -s -b cookies.txt 'https://chat.codyssey.run/api/me/chats?limit=2'
```

운영 서비스의 실제 응답입니다. 긴 답변은 앞부분만 남겼습니다.

```json
{
    "items": [
        {
            "id": 13,
            "session_id": 6,
            "session_title": "너 얼마나 똑똑해?",
            "question": "너 얼마나 똑똑해?",
            "answer": "좋은 질문이에요 — “똑똑함”은 여러 면에서 다르게 측정할 수 있어서 한 문장으로 딱 말하긴 어렵습니다. (생략)",
            "status": "ok",
            "error_code": null,
            "model_code": "gpt-5-mini",
            "billed_tokens": 640,
            "created_at": "2026-10-07T08:51:30.372179Z"
        },
        {
            "id": 11,
            "session_id": 5,
            "session_title": "안녕 너 이름이 뭐야",
            "question": "이제 니 이름이 뭐라고?",
            "answer": "지금은 jev예요. 편하게 그렇게 불러줘도 돼요. 다른 이름으로 바꾸고 싶으면 말해줘.",
            "status": "ok",
            "error_code": null,
            "model_code": "gpt-5-mini",
            "billed_tokens": 238,
            "created_at": "2026-10-07T08:50:50.261561Z"
        }
    ],
    "total": 7
}
```

관리자 계정은 전체 사용자의 대화를 조회할 수 있고, `user_id`로 특정 사용자만 조회할 수 있습니다. 응답 항목에는 `username`과 이름(`name`)이 추가됩니다.

```bash
curl -s -b admin-cookies.txt 'https://chat.codyssey.run/api/admin/chats?user_id=2&limit=5'
```

같은 내용은 웹 화면의 내 대화 기록(`/logs`)과 관리자 화면의 대화 로그 탭에서도 확인할 수 있습니다.

## 서버 로그와 오류 추적

API는 이벤트 이름 뒤에 `key=value` 필드를 붙인 한 줄 로그를 남깁니다. 값에 공백이나 `=`가 있으면 따옴표로 감쌉니다.

| 이벤트 | 시점 | 주요 필드 |
|---|---|---|
| `request_received` | 요청 수신. `/api/chat`은 로그인 사용자 확인 후 `user_id`와 함께 한 번 더 남깁니다 | `method`, `path`, `request_id`, `user_id` |
| `ai_call_start` | AI API 호출 직전 | `user_id`, `request_id`, `model` |
| `ai_call_success` | AI 응답 수신 | `request_id`, `latency_ms`, `tokens` |
| `ai_call_fail` | AI 호출 실패, 타임아웃 | `request_id`, `error_code`, `latency_ms` |
| `db_save_success` | 메시지 저장 성공 | `user_id`, `message_id` |
| `db_save_fail` | 메시지 저장 실패 | `user_id`, `error` |

`request_id`는 요청마다 만드는 12자리 값입니다. 같은 요청의 로그는 모두 같은 `request_id`를 가지며, 답변 메시지 행의 `messages.request_id`에도 저장되어 DB 기록과 서버 로그를 연결할 수 있습니다. 저장 로그에는 `request_id` 대신 `message_id`가 남으므로 `grep -A`로 뒤따르는 줄까지 함께 확인합니다.

### 오류 응답

| 코드 | 상태 | 상황 |
|---|---|---|
| `AI_TIMEOUT` | 504 | AI 응답이 `AI_TIMEOUT_SECONDS` 안에 오지 않음 |
| `AI_ERROR` | 502 | AI API 오류, 연결 실패 |
| `QUOTA_EXCEEDED` | 429 | 이번 달 사용량이 월 토큰 한도 이상 |

AI 호출이 실패하면 질문과 오류 안내 메시지를 `status=error`로 저장하고, 응답의 `detail`에 `session_id`를 함께 돌려줍니다. 화면은 이 값으로 실패한 질문이 남은 대화를 다시 불러옵니다. 할당량 초과는 AI를 호출하기 전에 차단하므로 메시지를 저장하지 않습니다.

아래는 로컬 실행 예시입니다.

### 정상 응답

```bash
docker compose logs api | grep -A4 request_id=f636d4068cbb
```

```
api-1  | 2026-10-07 09:17:43,242 INFO request_received method=POST path=/api/chat request_id=f636d4068cbb
api-1  | 2026-10-07 09:17:43,247 INFO request_received user_id=1 path=/api/chat request_id=f636d4068cbb
api-1  | 2026-10-07 09:17:43,255 INFO db_save_success user_id=1 message_id=1
api-1  | 2026-10-07 09:17:43,255 INFO ai_call_start user_id=1 request_id=f636d4068cbb model=gpt-5-mini
api-1  | 2026-10-07 09:17:49,695 INFO HTTP Request: POST https://copa.codyssey.kr/v1/chat/completions "HTTP/1.1 200 "
api-1  | 2026-10-07 09:17:49,706 INFO ai_call_success request_id=f636d4068cbb latency_ms=6450 tokens=738
api-1  | 2026-10-07 09:17:49,713 INFO db_save_success user_id=1 message_id=2
api-1  | INFO:     172.29.0.4:41458 - "POST /api/chat HTTP/1.1" 200 OK
```

### 타임아웃

`.env`에 `AI_TIMEOUT_SECONDS=1`을 넣고 `api` 컨테이너를 다시 만든 뒤 질문했습니다.

```bash
curl -s -w '\n%{http_code}\n' -b cookies.txt -H 'Content-Type: application/json' \
  -d '{"message":"TCP와 UDP 차이를 자세히 설명해줘"}' http://localhost:8081/api/chat
```

```
{"detail":{"code":"AI_TIMEOUT","message":"현재 응답이 지연되고 있어요. 잠시 후 다시 시도해 주세요.","session_id":2}}
504
```

```bash
docker compose logs api | grep -A4 request_id=0cbebe062a35
```

```
api-1  | 2026-10-07 09:18:22,570 INFO request_received method=POST path=/api/chat request_id=0cbebe062a35
api-1  | 2026-10-07 09:18:22,576 INFO request_received user_id=1 path=/api/chat request_id=0cbebe062a35
api-1  | 2026-10-07 09:18:22,584 INFO db_save_success user_id=1 message_id=3
api-1  | 2026-10-07 09:18:22,585 INFO ai_call_start user_id=1 request_id=0cbebe062a35 model=gpt-5-mini
api-1  | 2026-10-07 09:18:23,679 WARNING ai_call_fail request_id=0cbebe062a35 error_code=AI_TIMEOUT latency_ms=1093
api-1  | 2026-10-07 09:18:23,691 INFO db_save_success user_id=1 message_id=4
api-1  | INFO:     172.29.0.4:50224 - "POST /api/chat HTTP/1.1" 504 Gateway Timeout
```

### 할당량 초과

관리자 화면에서 월 토큰 한도를 100으로 낮춘 뒤 질문했습니다. 이번 달 사용량 369가 한도 이상이므로 AI를 호출하지 않고 429를 돌려줍니다.

```bash
curl -s -w '\n%{http_code}\n' -b cookies.txt -H 'Content-Type: application/json' \
  -d '{"message":"파이썬 GIL이 뭐야?"}' http://localhost:8081/api/chat
```

```
{"detail":{"code":"QUOTA_EXCEEDED","message":"이번 달 사용량을 모두 사용했습니다. 관리자에게 문의해 주세요."}}
429
```

```bash
docker compose logs api | grep -B2 -A1 quota_exceeded
```

```
api-1  | 2026-10-07 09:18:31,566 INFO request_received method=POST path=/api/chat request_id=368ee3600eed
api-1  | 2026-10-07 09:18:31,568 INFO request_received user_id=1 path=/api/chat request_id=368ee3600eed
api-1  | 2026-10-07 09:18:31,569 WARNING quota_exceeded user_id=1 month_used=369 token_limit=100
api-1  | INFO:     172.29.0.4:37116 - "POST /api/chat HTTP/1.1" 429 Too Many Requests
```

## 실행 방법

```bash
git clone https://github.com/innoaca-codyssey/B7-1.git
cd B7-1
cp .env.example .env
# .env 값 입력
docker compose up -d --build
```

브라우저에서 `http://localhost:8081`로 접속합니다.

### 환경 변수

| 이름 | 설명 | 기본값 |
|---|---|---|
| `POSTGRES_USER` | PostgreSQL 사용자 | |
| `POSTGRES_PASSWORD` | PostgreSQL 비밀번호 | |
| `POSTGRES_DB` | PostgreSQL DB 이름 | |
| `JWT_SECRET` | 로그인 토큰 서명 키. 32자 이상이어야 하며 짧으면 API가 시작되지 않습니다 | |
| `JWT_EXPIRE_MINUTES` | 로그인 유지 시간(분) | `1440` |
| `ADMIN_USERNAME` | 시작 시 생성할 관리자 아이디 | |
| `ADMIN_PASSWORD` | 시작 시 생성할 관리자 비밀번호. 8자 이상 72바이트 이하 | |
| `DEFAULT_TOKEN_LIMIT` | 신규 사용자의 월 토큰 한도 | `100000` |
| `AI_BASE_URL` | AI API 주소 | `https://copa.codyssey.kr/v1` |
| `AI_API_KEY` | AI API 키 | |
| `AI_TIMEOUT_SECONDS` | AI API 호출 타임아웃(초) | `30` |
| `CONTEXT_WINDOW` | AI에 함께 보내는 같은 대화의 최근 메시지 수 | `10` |
| `SMTP_HOST` | 인증 메일을 보낼 SMTP 서버 | |
| `SMTP_PORT` | SMTP 포트(STARTTLS) | `587` |
| `SMTP_USERNAME` | SMTP 사용자 | |
| `SMTP_PASSWORD` | SMTP 비밀번호 | |
| `MAIL_FROM` | 인증 메일 발신자 | |

`DATABASE_URL`은 Compose가 `POSTGRES_*` 값으로 만들어 `api` 컨테이너에 전달합니다. 값이 비어 있는 환경 변수는 설정하지 않은 것으로 처리합니다.

`ADMIN_USERNAME`과 `ADMIN_PASSWORD`가 둘 다 있으면 API 시작 시 관리자 계정을 생성합니다. 관리자 계정은 이메일 인증을 마친 상태로 생성됩니다. 같은 아이디의 관리자 계정이 이미 있으면 그대로 사용하고, 같은 아이디의 일반 계정이 이미 있으면 관리자 생성을 건너뛰고 `admin_seed_skipped` 경고 로그를 남깁니다.

`SMTP_HOST`가 비어 있으면 인증 메일을 보내지 않고 `mail_skipped` 경고 로그만 남깁니다. 메일 발송에 실패해도 회원가입은 완료되며, 인증 화면에서 코드를 다시 요청할 수 있습니다. 운영 환경은 Amazon SES의 SMTP 인터페이스를 사용합니다.

`.env`는 `.gitignore`에 포함되어 있습니다.

### 로컬 개발

```bash
docker run -d --name b7-1-test-db -e POSTGRES_USER=chatbot -e POSTGRES_PASSWORD=chatbot \
  -e POSTGRES_DB=chatbot_test -p 5433:5432 postgres:16-alpine

cd backend
uv sync
uv run pytest
DATABASE_URL=postgresql+psycopg://chatbot:chatbot@localhost:5433/chatbot_test \
  JWT_SECRET=<32자 이상 문자열> uv run uvicorn app.main:app --reload

cd ../frontend
npm ci
npm run dev
```

테스트는 `TEST_DATABASE_URL`(기본 `postgresql+psycopg://chatbot:chatbot@localhost:5433/chatbot_test`)의 DB를 사용하며, 테스트마다 테이블을 삭제하고 다시 생성합니다. 백엔드 설정은 실행 위치의 `.env`를 읽으므로 `backend/`에서 실행할 때는 저장소 루트의 `.env`가 적용되지 않습니다. Vite 개발 서버는 `/api` 요청을 `http://localhost:8000`으로 전달합니다.

## 팀 구성과 역할

| 이름 | GitHub | 역할 |
|---|---|---|
| 신예준 | pnuece | 백엔드 AI 연동, CI/CD |
| 정세영 | ashofrondol | 백엔드 인증, 세션, DB |
| 김희성 | Logan-kim-the-philosopher | 프론트엔드 |

### 개인별 작업 요약

- 신예준: 저장소 초기 구성과 이슈, PR 템플릿, AI API 설정과 호출 클라이언트(타임아웃, 오류 코드 변환), AI 모델 테이블과 초기 데이터, 프리셋 4종, 챗봇 질문 API와 AI 호출, DB 저장 실패 처리, 요청 로그와 `request_id`, 과금 토큰 계산과 월 사용량 차단, 관리자 모델 관리와 일별 사용량 API, CI 워크플로와 `main` 반영 시 배포
- 정세영: DB 연결과 테이블 모델, 회원가입과 로그인(bcrypt, JWT 쿠키), 현재 사용자와 관리자 권한 의존성, 대화 세션 API, 내 대화 로그 API와 `check_logs.sql`, 초기 관리자 계정, 관리자 사용자 관리와 대화 로그 API, 사용자 이름과 이메일 인증, README
- 김희성: React 프로젝트 구성과 API 요청 모듈, 로그인 상태 관리와 보호 라우트, 로그인과 회원가입 화면, 대화 목록과 채팅 화면(모델, 프리셋 선택, 4000자 제한, 오류 안내), 내 대화 기록 화면, 관리자 화면(사용자, 모델, 사용량, 대화 로그 탭), 프론트엔드 Dockerfile과 Nginx 설정, 화면 캡처

## 브랜치 전략

- `main`: 배포 기준 브랜치
- `develop`: 기능을 모으는 브랜치
- `feature/<기능>`: 기능 단위 작업 브랜치. `develop`으로 PR을 열고 리뷰 후 병합합니다.
