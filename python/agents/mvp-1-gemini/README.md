# 🤖 MVP-1 Gemini: 사용자 데이터 기반 질의 생성 에이전트

Gemini Fullstack 구조를 활용하여 재구현된 사용자 데이터 기반 질의 생성 및 리포트 생성 에이전트입니다.

## 📌 프로젝트 개요

MVP-1 Gemini는 Google ADK(Agent Development Kit)와 Gemini Fullstack 구조를 기반으로 한 데이터 분석 및 리포트 생성 에이전트입니다. 사용자가 제공하는 데이터 파일(CSV 또는 Excel)을 분석하고, 체계적인 데이터 검증과 분석을 통해 맞춤형 리포트를 생성합니다.

## 🎯 주요 기능

### 1. 데이터 확인 및 검증
- **사용자 요청 분석**: 자연어 요청을 분석하여 적절한 응답 제공
- **데이터 검증**: 파일 존재, 형식, 구조, 품질 종합 검증
- **데이터 분석**: CSV/Excel 파일 구조 및 내용 분석

### 2. 리포트 생성
- **포괄적인 분석**: 데이터 특성에 맞는 맞춤형 분석
- **구조화된 리포트**: 요약, 주요 발견사항, 데이터 분석, 결론 및 권장사항
- **다양한 출력 형식**: Markdown, HTML, TXT 형식 지원

### 3. Gemini Fullstack 구조 활용
- **React 프론트엔드**: 사용자 친화적인 웹 인터페이스
- **FastAPI 백엔드**: 고성능 API 서버
- **Google ADK**: 상태 관리 및 멀티 에이전트 워크플로우

## 🏗️ 아키텍처

### 에이전트 구조
- **메인 Agent**: `mvp_1_agent` - 메인 데이터 분석 및 리포트 생성 에이전트
- **서브 Agent**: `data_checker_agent` - 데이터 확인 및 검증 전용 에이전트
- **서브 Agent**: `report_generator_agent` - 리포트 생성 전용 에이전트
- **Gemini 모델**: `gemini-2.5-flash` - AI 모델

### 핵심 도구
- **UserDataCheckTool**: 사용자 요청 분석 및 적절한 응답 제공
- **DataValidationTool**: 사용자 데이터 준비 상태 검증 및 품질 평가
- **DataAnalysisTool**: CSV/Excel 파일 분석 및 스키마 추출

### 워크플로우
1. **사용자 요청 분석**: 사용자의 요청 유형 파악 (데이터 확인 vs 리포트 생성)
2. **데이터 파일 확인**: vdata 폴더의 데이터 파일 존재 및 형식 확인
3. **데이터 검증**: 파일 존재, 형식, 구조, 품질 검증
4. **데이터 분석**: 파일 구조 및 내용 분석
5. **리포트 생성**: 수집된 정보를 바탕으로 포괄적인 분석 리포트 자동 생성

## 📂 프로젝트 구조

```
mvp-1-gemini/
├── app/                              # 백엔드 애플리케이션
│   ├── __init__.py
│   ├── agent.py                     # 메인 에이전트 정의
│   ├── config.py                    # 설정 관리
│   └── tools/                       # 핵심 도구들
│       ├── __init__.py
│       ├── user_data_check_tool.py  # 사용자 요청 분석 도구
│       ├── data_validation_tool.py  # 데이터 검증 도구
│       └── data_analysis_tool.py    # 데이터 분석 도구
├── frontend/                         # React 프론트엔드
│   ├── src/
│   │   ├── components/              # UI 컴포넌트
│   │   ├── App.tsx                  # 메인 앱 컴포넌트
│   │   └── main.tsx                 # 앱 진입점
│   ├── package.json                 # 프론트엔드 의존성
│   └── vite.config.ts               # Vite 설정
├── data/                            # 데이터 파일 저장소
│   └── vdata/                       # 사용자 데이터 파일
├── .env.example                     # 환경 변수 예시
├── Makefile                         # 빌드 및 실행 스크립트
├── pyproject.toml                   # Python 프로젝트 설정
└── README.md                        # 프로젝트 문서
```

## 🚀 설치 및 실행

### 1. 초기 설정
```bash
# 프로젝트 디렉토리로 이동
cd /Users/khk/work/connev/adk-samples/python/agents/mvp-1-gemini

# 의존성 설치
make install
```

### 2. 환경 변수 설정
`.env` 파일을 생성하여 Google API 키를 설정하세요:
```bash
cp .env.example .env
# .env 파일 편집
GOOGLE_GENAI_USE_VERTEXAI=FALSE
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 3. 실행 방법

#### 방법 1: 개별 실행 (권장)
**터미널 1 - 백엔드 서버 실행:**
```bash
cd /Users/khk/work/connev/adk-samples/python/agents/mvp-1-gemini
uv run adk api_server app --allow_origins="*"
```

**터미널 2 - 프론트엔드 서버 실행:**
```bash
cd /Users/khk/work/connev/adk-samples/python/agents/mvp-1-gemini
npm --prefix frontend run dev
```

#### 방법 2: Makefile 사용
```bash
# 백엔드만 실행
make dev-backend

# 프론트엔드만 실행 (새 터미널에서)
make dev-frontend
```

### 4. 접속 확인
- **프론트엔드**: http://localhost:5173
- **백엔드 API**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs

### 5. 문제 해결
만약 포트 충돌이 발생하면:
```bash
# 실행 중인 프로세스 종료
pkill -f "adk api_server"
pkill -f "vite"

# 다시 실행
uv run adk api_server app --allow_origins="*"
```

## 🔍 사용 예시

### 1. 데이터 확인 요청
```
사용자: "데이터 확인해줘"
에이전트: "네, 데이터 상태를 확인해드리겠습니다! 📊
현재 'data/vdata' 디렉토리의 데이터를 검증하겠습니다."
→ DataValidationTool 실행하여 데이터 검증 결과 제공
```

### 2. 리포트 생성 요청
```
사용자: "리포트를 만들어줘"
에이전트: "리포트 생성을 도와드리겠습니다! 📈
vdata 폴더의 데이터를 사용하여 맞춤형 리포트를 생성하겠습니다."
→ 데이터 검증 후 리포트 생성 프로세스 진행
```

### 3. 웹 인터페이스 사용
- React 기반의 직관적인 웹 인터페이스
- 실시간 채팅 형태의 상호작용
- 데이터 업로드 및 분석 결과 시각화
- 리포트 다운로드 기능

## 🔧 기술 스택

### Backend
- **Google ADK**: Agent Development Kit
- **FastAPI**: 고성능 웹 프레임워크
- **Google Gemini**: AI 모델 (gemini-2.5-flash)
- **Pandas**: 데이터 처리 및 분석
- **openpyxl**: Excel 파일 처리

### Frontend
- **React**: 사용자 인터페이스 라이브러리
- **Vite**: 빠른 빌드 도구
- **Tailwind CSS**: 유틸리티 우선 CSS 프레임워크
- **Shadcn UI**: 접근성이 뛰어난 UI 컴포넌트

## 📊 데이터 지원

### 지원 파일 형식
- **CSV**: 쉼표로 구분된 값 파일
- **Excel**: .xlsx, .xls 형식

### 데이터 디렉토리
- 기본 경로: `data/vdata/`
- 자동 파일 탐지 기능
- 다중 파일 지원

## ⚙️ 설정 옵션

### 환경 변수
- `GOOGLE_GENAI_USE_VERTEXAI`: Vertex AI 사용 여부 (기본값: True)
- `GOOGLE_API_KEY`: Google AI Studio API 키 (Vertex AI 사용 시 불필요)
- `GOOGLE_CLOUD_PROJECT`: Google Cloud 프로젝트 ID
- `GOOGLE_CLOUD_LOCATION`: Google Cloud 리전

### 모델 설정
- **Worker Model**: gemini-2.5-flash (작업용)
- **Critic Model**: gemini-2.5-pro (평가용)
- **최대 분석 반복**: 3회

## 🚨 주의사항

1. **Google API 키 필요**: Google Gemini API 키가 필요합니다.
2. **지원 형식**: CSV와 Excel 파일을 지원합니다.
3. **데이터 크기**: 대용량 파일의 경우 처리 시간이 오래 걸릴 수 있습니다.
4. **브라우저 지원**: 최신 브라우저 사용을 권장합니다.

## 🤝 기여하기

1. 이슈 리포트: 버그나 개선 사항을 이슈로 등록
2. 풀 리퀘스트: 새로운 기능이나 버그 수정 제안
3. 문서 개선: README나 코드 주석 개선

## 📄 라이선스

Apache License 2.0

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.

---

**MVP-1 Gemini**는 Gemini Fullstack의 강력한 구조를 활용하여 데이터 분석과 리포트 생성을 더욱 효율적이고 사용자 친화적으로 만듭니다.