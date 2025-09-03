# Document Question & Report Agent Frontend

Vue.js 3 기반의 프론트엔드 애플리케이션입니다.

## 🚀 주요 기능

- **단계별 워크플로우**: 문서 업로드 → 질문 생성 → 질문 선택 → 리포트 생성 → 다운로드
- **반응형 디자인**: 모바일과 데스크톱 모두 지원
- **실시간 진행률**: 각 단계별 진행 상황을 시각적으로 표시
- **다양한 출력 형식**: PDF, Word, HTML, PowerPoint 지원

## 🛠️ 기술 스택

- **Vue.js 3**: Composition API 기반
- **Element Plus**: UI 컴포넌트 라이브러리
- **Vue Router**: 페이지 라우팅
- **Axios**: HTTP 클라이언트

## 📁 프로젝트 구조

```
src/
├── views/                    # 페이지 컴포넌트
│   ├── Home.vue            # 홈 화면
│   ├── DocumentUpload.vue  # 문서 업로드
│   ├── QuestionGeneration.vue # 질문 생성 및 선택
│   └── ReportGeneration.vue   # 리포트 생성 및 다운로드
├── router/                  # 라우터 설정
├── App.vue                  # 메인 앱 컴포넌트
└── main.js                  # 앱 진입점
```

## 🚀 실행 방법

### 개발 환경

```bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev
# 또는
npm run serve
```

### 프로덕션 빌드

```bash
# 프로덕션 빌드
npm run build:prod

# 빌드 결과 미리보기
npm run preview
```

## ⚙️ 환경 설정

### 개발 환경 (.env)
```
VUE_APP_API_URL=http://localhost:8000/api
NODE_ENV=development
```

### 프로덕션 환경 (.env.production)
```
VUE_APP_API_URL=/api
NODE_ENV=production
```

## 🔧 API 연동

프론트엔드는 다음 API 엔드포인트와 연동됩니다:

- `POST /api/upload` - 문서 업로드 및 분석
- `GET /api/questions/{document_id}` - 질문 세트 생성
- `POST /api/report` - 리포트 생성
- `POST /api/report/{draft_id}/finalize` - 리포트 최종화

## 📱 반응형 디자인

- **데스크톱**: 1200px 이상
- **태블릿**: 768px - 1199px
- **모바일**: 767px 이하

## 🎨 UI/UX 특징

- **단계별 진행 표시**: 사용자가 현재 위치를 명확히 파악
- **실시간 피드백**: 각 작업의 진행 상황을 시각적으로 표시
- **직관적인 인터페이스**: 체크박스 기반의 질문 선택
- **다양한 다운로드 옵션**: 사용자 요구에 맞는 출력 형식 제공

## 🐛 문제 해결

### API 연결 오류
1. 백엔드 서버가 실행 중인지 확인
2. `.env` 파일의 `VUE_APP_API_URL` 설정 확인
3. CORS 설정 확인

### 빌드 오류
1. Node.js 버전 확인 (16.x 이상 권장)
2. `npm install` 재실행
3. `node_modules` 삭제 후 재설치

## 📄 라이선스

MIT License