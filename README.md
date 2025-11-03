# Jira API Proxy

JetBrains IDE와 호환되는 Jira API Proxy 서버입니다. 이 프록시 서버를 통해 JetBrains IDE (IntelliJ IDEA, PyCharm 등)의 Task Management 기능을 실제 Jira 서버와 연동할 수 있습니다. 요청별 인증을 지원하여 보안성이 향상되었습니다.

## 주요 기능

- ✅ Jira REST API v2 호환 엔드포인트 제공
- ✅ JetBrains IDE Task Management 완벽 지원
- ✅ 요청별 Basic/Bearer Token 인증 지원 (더 이상 환경변수에 자격증명 저장 불필요)
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
# Jira Configuration - 인증은 요청별로 처리됩니다
JIRA_BASE_URL=https://your-jira-instance.atlassian.net

# Proxy Server Configuration
PROXY_HOST=0.0.0.0
PROXY_PORT=8000
DEBUG=true

# 참고: 인증 정보는 더 이상 환경변수에 설정하지 않습니다.
# 대신 각 API 요청의 Authorization 헤더를 통해 전달됩니다.
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
   - **Username**: Jira 사용자명 (Basic 인증용)
   - **Password**: Jira API 토큰 또는 비밀번호
   - **참고**: 인증 정보는 각 요청의 Authorization 헤더로 전달되어 보안이 강화되었습니다

### 설정 예시

```
Server URL: http://localhost:8000
Username: john.doe@company.com
Password: your-jira-api-token
```

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
│   ├── config.py            # 설정 관리
│   ├── exceptions.py        # 커스텀 예외 클래스
│   ├── middleware.py        # 미들웨어 (로깅, 보안 헤더)
│   ├── error_handlers.py    # 전역 에러 핸들러
│   ├── models/
│   │   ├── __init__.py
│   │   └── jira.py          # Jira API 데이터 모델
│   ├── services/
│   │   ├── __init__.py
│   │   └── jira_client.py   # Jira API 클라이언트
│   └── routers/
│       ├── __init__.py
│       └── jira_api.py      # API 라우터
├── main.py                  # 애플리케이션 실행 스크립트
├── pyproject.toml          # Python 프로젝트 설정
├── Dockerfile              # Docker 이미지 빌드 설정
├── docker-compose.yml      # Docker Compose 설정
├── .env.example            # 환경변수 예시 파일
└── README.md              # 프로젝트 문서
```

## 보안 고려사항

- API 토큰을 환경변수로 관리하여 보안 유지
- CORS 설정을 운영 환경에 맞게 조정
- HTTPS 사용 권장 (운영 환경)
- 보안 헤더 자동 추가 (X-Content-Type-Options, X-Frame-Options 등)

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
   - `.env` 파일의 `JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_PASSWORD` 확인
   - Jira API 토큰이 올바른지 확인
   - 네트워크 연결 상태 확인

2. **JetBrains IDE에서 인식하지 못함**
   - 프록시 서버가 정상 실행 중인지 확인
   - IDE에서 설정한 서버 URL이 정확한지 확인
   - Health Check 엔드포인트 확인: `http://localhost:8000/rest/api/2/health`

3. **권한 오류**
   - Jira 사용자 계정의 권한 확인
   - API 토큰의 유효성 확인

### 디버깅

Debug 모드 활성화:
```env
DEBUG=true
```

이렇게 하면 상세한 로그와 API 문서(`/docs`)에 접근할 수 있습니다.

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.