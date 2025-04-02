# 농산물 가격 정보 API 백엔드

농산물 가격 정보 및 예측, 커뮤니티 기능을 제공하는 백엔드 API 서버입니다.

## 프로젝트 구조

```
back/
├── app.py              # 메인 애플리케이션
├── backend.py          # 백엔드 로직
├── chatbot.py          # 챗봇 기능
├── weather.py          # 날씨 관련 기능
├── image_classifier.py # 이미지 분석
├── routes/            # API 라우트
├── utils/             # 유틸리티 함수
├── services/          # 서비스 로직
├── pricedata/         # 가격 데이터
├── pricepython/       # 가격 예측 모델
└── db.sql             # 데이터베이스 스키마
```

## 기술 스택

- Python
- FastAPI
- PostgreSQL
- JWT 인증
- ONNX Runtime (이미지 분석)

## 주요 기능

### 1. 농산물 정보

- 도시별 날씨 정보 조회 (`weather.py`)
- 참외 질병 예측 (`image_classifier.py`)
- 작물 가격 예측 (`pricepython/`)
- 실시간 농산물 가격 정보 (`pricedata/`)
- 시장 정보 조회

### 2. 사용자 관리

- 회원가입
- 로그인/로그아웃 (JWT 인증)
- 사용자 프로필 관리

### 3. 커뮤니티

- 게시글 작성/조회/수정/삭제
- 댓글 작성/조회
- 카테고리별 게시판
  - 텃밭 정보
  - 농산물 마켓
  - 자유게시판

## 시작하기

### 사전 요구사항

- Python 3.8 이상
- PostgreSQL
- Node.js (일부 기능에 필요)

### 설치 및 실행

1. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치

```bash
pip install -r requirements.txt
npm install  # 일부 기능에 필요한 Node.js 패키지 설치
```

3. 환경 변수 설정
   `.env` 파일을 생성하고 다음 내용을 설정하세요:

```
DB_HOST=localhost
DB_USER=your_db_user
DB_PASS=your_db_password
DB_NAME=your_db_name
DB_PORT=5432
JWT_SECRET=your_jwt_secret
```

4. 데이터베이스 설정

```bash
psql -U your_db_user -d your_db_name -f db.sql
```

5. 서버 실행

```bash
uvicorn app:app --reload
```

서버는 기본적으로 http://localhost:8000 에서 실행됩니다.

## API 문서

API 문서는 서버 실행 후 다음 URL에서 확인할 수 있습니다:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 엔드포인트

### 농산물 정보

- GET `/api/weather` - 도시별 날씨 정보
- POST `/api/disease/predict` - 질병 이미지 분석
- GET `/api/price/predict` - 작물 가격 예측
- GET `/api/price/current` - 실시간 가격 정보

### 사용자 관리

- POST `/api/auth/register` - 회원가입
- POST `/api/auth/login` - 로그인
- GET `/api/auth/profile` - 프로필 조회
- PUT `/api/auth/profile` - 프로필 수정

### 커뮤니티

- GET `/api/posts` - 게시글 목록
- POST `/api/posts` - 게시글 작성
- GET `/api/posts/{id}` - 게시글 조회
- PUT `/api/posts/{id}` - 게시글 수정
- DELETE `/api/posts/{id}` - 게시글 삭제

## 테스트

테스트를 실행하려면:

```bash
python -m pytest
```

## 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다.
