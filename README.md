# B7-1 웹 기반 AI 챗봇 서비스

사용자 문의에 실시간으로 응답하는 AI 챗봇 서비스입니다. 로그인한 사용자가 웹 화면에서 질문하면 서버가 AI API를 호출해 응답을 생성하고, 같은 화면에 답변을 표시합니다. 질문과 답변은 PostgreSQL에 사용자별로 누적 저장되며, 같은 대화의 최근 메시지를 함께 보내 이전 질문을 이어서 물어볼 수 있습니다.

서비스 주소: https://chat.codyssey.run

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

### 채팅

![채팅](docs/images/chat-view.png)

왼쪽은 대화 목록, 오른쪽은 선택한 대화의 메시지입니다. 입력창 위에서 모델과 프리셋(학습 튜터, 코드 리뷰어, 디버깅 도우미, 개념 설명)을 선택합니다. 답변은 마크다운으로 표시되고, 메시지마다 과금 토큰 수가 표시됩니다.

![대화 목록](docs/images/session-sidebar.png)

AI 호출이 실패하거나 시간이 초과되면 오류 코드와 안내 문구가 대화에 함께 남습니다.

![오류 안내](docs/images/chat-error.png)

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

## 팀 구성

| 이름 | GitHub | 역할 |
|---|---|---|
| 신예준 | pnuece | 백엔드 AI 연동 |
| 정세영 | JeongSeYoung | 백엔드 인증, 세션, DB |
| 김희성 | Logan-kim-the-philosopher | 프론트엔드 |

## 브랜치 전략

- `main`: 배포 기준 브랜치
- `develop`: 기능을 모으는 브랜치
- `feature/<기능>`: 기능 단위 작업 브랜치. `develop`으로 PR을 열고 리뷰 후 병합합니다.
