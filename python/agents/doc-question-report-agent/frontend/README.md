# Document Question & Report Agent Frontend

Vue.js 3 기반의 프론트엔드 애플리케이션입니다.

## 🚀 기능

- **문서 업로드**: PDF, DOCX, Excel, CSV 등 다양한 형식 지원
- **질문 생성**: AI 기반 자동 질문 생성
- **리포트 생성**: 선택된 질문을 바탕으로 전문 리포트 생성
- **반응형 디자인**: 모바일과 데스크톱 모두 지원
- **실시간 상태 확인**: API 서버 상태 모니터링

## 🛠️ 기술 스택

- **Vue.js 3**: 최신 Vue.js 프레임워크
- **Element Plus**: UI 컴포넌트 라이브러리
- **Vue Router**: 클라이언트 사이드 라우팅
- **Axios**: HTTP 클라이언트
- **SCSS**: CSS 전처리기

## 📦 설치 및 실행

### 1. 의존성 설치
```bash
npm install
```

### 2. 개발 서버 실행
```bash
npm run serve
```

### 3. 프로덕션 빌드
```bash
npm run build
```

## 🌐 접속 방법

- **개발 환경**: http://localhost:3000
- **백엔드 API**: http://localhost:8000

## 📁 프로젝트 구조

```
frontend/
├── public/                 # 정적 파일
├── src/
│   ├── components/         # 재사용 가능한 컴포넌트
│   ├── views/             # 페이지 컴포넌트
│   ├── router/            # 라우팅 설정
│   ├── App.vue            # 메인 앱 컴포넌트
│   └── main.js            # 앱 진입점
├── package.json           # 프로젝트 설정
└── vue.config.js          # Vue CLI 설정
```

## 🔧 환경 설정

### 백엔드 API 연결
프론트엔드는 `http://localhost:8000`의 백엔드 API와 통신합니다.

### 프록시 설정
개발 환경에서는 `/api` 경로를 통해 백엔드로 프록시됩니다.

## 📱 반응형 디자인

- **데스크톱**: 1200px 이상
- **태블릿**: 768px - 1199px
- **모바일**: 767px 이하

## 🎨 UI/UX 특징

- **모던한 디자인**: Element Plus 컴포넌트 활용
- **직관적인 워크플로우**: 3단계 프로세스 (업로드 → 질문 → 리포트)
- **실시간 피드백**: 로딩 상태 및 진행률 표시
- **접근성**: 키보드 네비게이션 및 스크린 리더 지원

## 🚀 배포

### Docker 배포
```bash
# 이미지 빌드
docker build -t doc-agent-frontend .

# 컨테이너 실행
docker run -p 80:80 doc-agent-frontend
```

### 정적 호스팅
```bash
npm run build
# dist/ 폴더를 웹 서버에 업로드
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.