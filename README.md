# Jira API Proxy

JetBrains IDE와 호환되는 Jira API Proxy 서버입니다. 이 프록시 서버를 통해 JetBrains IDE (IntelliJ IDEA, PyCharm 등)의 Task Management 기능을 실제 Jira 서버와 연동할 수 있습니다. 이중 인증(Dual Authentication) 모드를 지원하여 API 인증과 사용자 활동 추적을 분리할 수 있습니다.

## 주요 기능

- ✅ Jira REST API v2 호환 엔드포인트 제공
- ✅ JetBrains IDE Task Management 완벽 지원
- ✅ **이중 인증 (Dual Authentication) 모드**
  - 서비스 계정을 통한 중앙화된 API 인증
  - 요청한 사용자의 활동 추적 (Jira Activity에 실제 사용자 기록)
  - 사용자 가장(User Impersonation) 지원 (Jira Server/Data Center)
- ✅ Docker 컨테이너 지원
- ✅ 종합적인 에러 핸들링 및 로깅
- ✅ CORS 및 보안 헤더 지원
- ✅ Health Check 엔드포인트

## 지원하는 API 엔드포인트

### 서버 정보
- `GET /rest/api/2/serverInfo` - Jira 서버 정보 조회

### 이슈 관리
- `GET /rest/api/2/search` - JQL을 사용한 이슈 검색
- `GET /rest/api/2/issue/{issue-key}` - 특정 이슈 조회
- `PUT /rest/api/2/issue/{issue-key}` - 이슈 업데이트
- `POST /rest/api/2/issue` - 새 이슈 생성

### 이슈 상태 변경
- `GET /rest/api/2/issue/{issue-key}/transitions` - 사용 가능한 상태 변경 목록 조회
- `POST /rest/api/2/issue/{issue-key}/transitions` - 이슈 상태 변경

### 프로젝트 관리
- `GET /rest/api/2/project` - 프로젝트 목록 조회
- `GET /rest/api/2/project/{project-key}` - 특정 프로젝트 조회

### 기타
- `GET /rest/api/2/health` - 프록시 서버 및 Jira 연결 상태 확인

## 설치 및 실행

### 환경 설정

1. `.env.example` 파일을 `.env`로 복사하고 설정값을 수정하세요:

```bash
cp .env.example .env
```

`.env` 파일 예시:
```env
# Jira Configuration
JIRA_BASE_URL=https://your-jira-instance.atlassian.net

# Service Account Credentials (for API authentication)
# 이 계정의 자격증명으로 Jira API에 인증합니다
JIRA_SERVICE_USERNAME=service-account@example.com
JIRA_SERVICE_API_TOKEN=your-service-account-api-token

# Proxy Server Configuration
PROXY_HOST=0.0.0.0
PROXY_PORT=8000
DEBUG=true

# 이중 인증 모드:
# - API 호출은 위의 서비스 계정 자격증명 사용
# - Activity 추적은 Authorization 헤더의 사용자 정보 사용
# - 이를 통해 중앙화된 인증과 개별 사용자 책임 추적을 동시에 지원
```

### Docker로 실행 (권장)

```bash
# 이미지 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d
```

### 로컬 환경에서 실행

```bash
# 의존성 설치
pip install -e .

# 개발 서버 실행
python main.py

# 또는 uvicorn으로 직접 실행
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## JetBrains IDE 설정

1. JetBrains IDE (IntelliJ IDEA, PyCharm 등)를 엽니다
2. `File → Settings` (Windows/Linux) 또는 `Preferences` (macOS)로 이동
3. `Tools → Tasks` 섹션 선택
4. `+` 버튼을 클릭하여 새 서버 추가
5. `Generic` 또는 `JIRA` 선택
6. 다음 설정을 입력:
   - **Server URL**: `http://localhost:8000` (또는 프록시 서버 주소)
   - **Username**: 실제 Jira 사용자명 (Activity 추적용)
   - **Password**: 실제 사용자의 Jira API 토큰
   - **참고**:
     - 프록시는 `.env`의 서비스 계정으로 Jira에 인증합니다
     - IDE에서 입력한 사용자 정보는 Activity 기록에 사용됩니다
     - 이중 인증을 통해 중앙 관리와 사용자 책임 추적이 가능합니다

### 설정 예시

```
Server URL: http://localhost:8000
Username: john.doe@company.com  ← Activity에 기록될 실제 사용자
Password: user-api-token        ← 사용자 식별용 (API 인증은 서비스 계정 사용)
```

### 이중 인증 모드 작동 방식

1. **IDE에서 요청**: 사용자가 JetBrains IDE에서 이슈 상태를 변경
2. **프록시 수신**: Authorization 헤더에서 사용자명 추출 (`john.doe@company.com`)
3. **Jira API 호출**:
   - 인증: `.env`의 서비스 계정 자격증명 사용
   - 사용자 가장: `X-Atlassian-User` 헤더에 `john.doe@company.com` 전달
4. **Jira Activity**: 실제 작업자로 `john.doe@company.com`이 기록됨

**참고**: 사용자 가장(User Impersonation) 기능은 Jira Server/Data Center에서 관리자 권한이 필요합니다. Jira Cloud에서는 제한적으로 지원됩니다.

## API 사용 예시

### 서버 정보 조회
```bash
curl -X GET "http://localhost:8000/rest/api/2/serverInfo"
```

### 이슈 검색
```bash
curl -X GET "http://localhost:8000/rest/api/2/search?jql=project=PROJ&maxResults=10"
```

### 특정 이슈 조회
```bash
curl -X GET "http://localhost:8000/rest/api/2/issue/PROJ-123"
```

### 이슈 상태 변경
```bash
curl -X POST "http://localhost:8000/rest/api/2/issue/PROJ-123/transitions" \
     -H "Content-Type: application/json" \
     -d '{"transition": {"id": "11"}}'
```

## 프로젝트 구조

```
JiraProxy/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 애플리케이션 진입점
│   ├── config.py            # 설정 관리 (이중 인증 설정 포함)
│   ├── utils.py             # 유틸리티 함수 (사용자 추출, 헤더 생성)
│   ├── exceptions.py        # 커스텀 예외 클래스
│   ├── middleware.py        # 미들웨어 (로깅, 보안 헤더)
│   ├── error_handlers.py    # 전역 에러 핸들러
│   ├── models/
│   │   ├── __init__.py
│   │   └── jira.py          # Jira API 데이터 모델
│   ├── services/
│   │   ├── __init__.py
│   │   └── jira_client.py   # Jira API 클라이언트 (이중 인증 지원)
│   └── routers/
│       ├── __init__.py
│       ├── jira_api.py      # API 라우터 (API v2)
│       └── latest_api.py    # API 라우터 (latest - JetBrains 호환)
├── main.py                  # 애플리케이션 실행 스크립트
├── pyproject.toml          # Python 프로젝트 설정
├── Dockerfile              # Docker 이미지 빌드 설정
├── docker-compose.yml      # Docker Compose 설정
├── .env.example            # 환경변수 예시 파일
└── README.md              # 프로젝트 문서
```

## 이중 인증 모드 (Dual Authentication)

### 개요
이중 인증 모드는 API 인증과 사용자 활동 추적을 분리하여 다음과 같은 이점을 제공합니다:

- **중앙화된 API 인증**: 모든 API 호출은 서비스 계정의 자격증명 사용
- **개별 사용자 책임 추적**: Jira Activity에 실제 작업을 수행한 사용자 기록
- **보안 강화**: 개별 사용자의 API 토큰을 관리할 필요 없음
- **감사 추적**: 누가 어떤 작업을 했는지 명확히 추적 가능

### 설정 방법

1. `.env` 파일에 서비스 계정 자격증명 설정:
```env
JIRA_SERVICE_USERNAME=service-account@company.com
JIRA_SERVICE_API_TOKEN=service-account-api-token
```

2. JetBrains IDE에서 실제 사용자 정보로 로그인

3. 프록시가 자동으로:
   - 서비스 계정으로 Jira API에 인증
   - 사용자 정보를 `X-Atlassian-User` 헤더로 전달하여 Activity 기록

### 지원 플랫폼

| Jira 플랫폼 | 지원 여부 | 요구사항 |
|------------|----------|---------|
| Jira Server/Data Center | ✅ 완전 지원 | 서비스 계정에 관리자 권한 필요 |
| Jira Cloud | ⚠️ 제한적 지원 | 사용자 가장 기능 제한적 |

### 기술적 구현

- **인증 헤더**: `Authorization: Basic <service-account-credentials>`
- **가장 헤더**: `X-Atlassian-User: <actual-user-email>`
- **사용자 추출**: Authorization 헤더에서 Base64 디코딩하여 사용자명 추출

## 보안 고려사항

- **서비스 계정 보안**: `.env` 파일의 서비스 계정 자격증명을 안전하게 관리
- **권한 관리**: 서비스 계정에 필요한 최소 권한만 부여 (최소 권한 원칙)
- **사용자 검증**: 실제 사용자 권한도 Jira에서 검증됨
- **CORS 설정**: 운영 환경에 맞게 CORS 설정 조정
- **HTTPS 사용**: 운영 환경에서는 반드시 HTTPS 사용
- **보안 헤더**: X-Content-Type-Options, X-Frame-Options 등 자동 추가
- **로그 필터링**: 민감한 정보(password, token, authorization) 자동 필터링

## 개발

### 의존성 설치
```bash
pip install -e .
```

### 테스트 실행
```bash
# API 테스트 (test_main.http 파일 사용)
# JetBrains IDE에서 HTTP 클라이언트로 실행
```

### 로그 확인
```bash
# Docker 컨테이너 로그
docker-compose logs -f

# 로컬 실행 시 콘솔에 출력됨
```

## 문제 해결

### 일반적인 문제

1. **Jira 연결 실패**
   - `.env` 파일의 `JIRA_BASE_URL`, `JIRA_SERVICE_USERNAME`, `JIRA_SERVICE_API_TOKEN` 확인
   - 서비스 계정의 Jira API 토큰이 올바른지 확인
   - 네트워크 연결 상태 확인

2. **JetBrains IDE에서 인식하지 못함**
   - 프록시 서버가 정상 실행 중인지 확인
   - IDE에서 설정한 서버 URL이 정확한지 확인
   - Health Check 엔드포인트 확인: `http://localhost:8000/rest/api/2/health`

3. **권한 오류**
   - 서비스 계정의 권한 확인 (관리자 권한 필요 시)
   - 실제 사용자 계정의 Jira 권한 확인
   - API 토큰의 유효성 확인

4. **사용자 가장(User Impersonation)이 작동하지 않음**
   - Jira Server/Data Center 사용 중인지 확인 (Jira Cloud는 제한적 지원)
   - 서비스 계정에 관리자 권한이 있는지 확인
   - 로그에서 `X-Atlassian-User` 헤더가 전송되는지 확인
   - Jira에서 사용자 가장 기능이 활성화되어 있는지 확인

### 디버깅

Debug 모드 활성화:
```env
DEBUG=true
```

이렇게 하면 상세한 로그와 API 문서(`/docs`)에 접근할 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.