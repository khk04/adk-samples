# 📊 MVP Report Generator

데이터 기반 자동 리포트 생성 MVP - CSV 데이터를 분석하여 한국어 리포트를 자동 생성하고 품질을 평가합니다.

## 📌 프로젝트 개요

이 프로젝트는 Google ADK(Agent Development Kit)를 기반으로 한 데이터 기반 자동 리포트 생성 시스템입니다. CSV 데이터를 업로드하면 자동으로 분석하여 한국어 비즈니스 리포트를 생성하고, 4가지 기준으로 품질을 평가하여 임계값에 도달할 때까지 반복 개선합니다.

## 🏗️ 아키텍처

### 에이전트 구조
- **LoopAgent**: `mvp_report_generator` - 메인 루프 에이전트
- **SequentialAgent**: `report_generation_evaluation_agent` - 리포트 생성 및 평가 순차 실행
- **Report Generation Agent**: CSV 데이터 분석 및 리포트 생성
- **Report Evaluation Agent**: 리포트 품질 평가
- **Checker Agent**: 루프 종료 조건 확인

### 워크플로우
1. **CSV 데이터 분석**: 업로드된 CSV 파일을 pandas로 분석
2. **리포트 생성**: 분석된 데이터를 바탕으로 한국어 리포트 생성
3. **품질 평가**: 4가지 기준으로 리포트 품질 평가 (0-10점)
4. **조건 확인**: 품질 점수가 임계값(8.0점) 이상이거나 최대 반복 횟수(3회) 도달 시 종료
5. **반복 개선**: 조건 미충족 시 1-4단계 반복

## 📂 프로젝트 구조

```
mvp/
├── data/                           # 데이터 파일 저장소
│   ├── sample_sales_data.csv       # 샘플 판매 데이터 (30개 레코드)
│   └── reports/                    # 생성된 리포트 저장 위치
├── mvp_agent/                      # 메인 에이전트 폴더
│   ├── __init__.py
│   ├── agent.py                    # 루트 에이전트 (LoopAgent)
│   ├── config.py                   # 설정 파일
│   ├── policy.json                 # 정책 파일 (평가 기준)
│   ├── prompt.py                   # 프롬프트 관리
│   ├── tools/                      # 도구들
│   │   ├── csv_analysis_tool.py    # CSV 데이터 분석 도구
│   │   ├── report_generation_tool.py # 리포트 생성 도구
│   │   ├── report_evaluation_tool.py # 리포트 평가 도구
│   │   └── condition_checker_tool.py # 조건 확인 도구
│   └── sub_agents/                 # 서브 에이전트들
│       ├── generation/             # 리포트 생성 에이전트
│       │   └── report_generation_agent.py
│       └── evaluation/             # 리포트 평가 에이전트
│           └── report_evaluation_agent.py
├── .env                            # 환경 변수
├── .env.example                    # 환경 변수 예시
├── main.py                         # FastAPI 웹 서버
├── setup.sh                        # 초기 설정 스크립트
├── start_web.sh                    # 웹 서버 시작 스크립트
├── pyproject.toml                  # Poetry 설정
└── README.md                       # 프로젝트 문서
```

## 🚀 주요 기능

### 1. CSV 데이터 분석
- 판매량, 매출, 지역별, 제품별 통계 분석
- 고객 등급별 분석
- 월별 트렌드 분석
- pandas 기반 데이터 처리

### 2. 자동 리포트 생성
- 한국어 비즈니스 리포트 자동 생성
- 구조화된 리포트 형식 (요약, 주요 발견사항, 데이터 분석, 결론 및 권장사항)
- 데이터 기반 인사이트 제공

### 3. 품질 평가 시스템
- **완성도 (30%)**: 필수 섹션 포함 여부
- **명확성 (25%)**: 내용의 명확성과 이해도
- **정확성 (25%)**: 데이터 분석의 정확성
- **구조 (20%)**: 리포트 구조의 논리성

### 4. 반복 개선
- 품질이 임계값(8.0/10)에 도달할 때까지 자동 반복
- 최대 3회 반복 후 자동 종료
- 각 반복마다 품질 점수 추적

## 🔧 기술 스택

- **Google ADK**: Agent Development Kit
- **LoopAgent**: 반복 실행 에이전트
- **Pandas**: CSV 데이터 처리
- **Poetry**: 의존성 관리
- **FastAPI**: 웹 서버
- **Google Gemini**: AI 모델

## 📊 샘플 데이터

`sample_sales_data.csv`에는 30개의 판매 레코드가 포함되어 있습니다:
- **컬럼**: 날짜, 제품명, 카테고리, 판매량, 단가, 총매출, 지역, 고객등급
- **제품**: 노트북, 스마트폰, 태블릿, 무선이어폰, 스마트워치
- **지역**: 서울, 부산, 대구, 인천, 광주, 대전
- **고객등급**: 프리미엄, 일반

## 🛠️ 설치 및 실행

### 1. 초기 설정
```bash
# 프로젝트 디렉토리로 이동
cd /home/khk/work/adk-samples/python/agents/mvp

# 초기 설정 스크립트 실행
chmod +x setup.sh
./setup.sh
```

### 2. 환경 변수 설정
`.env` 파일을 편집하여 Google API 키를 설정하세요:
```bash
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_GENAI_USE_VERTEXAI=0
QUALITY_THRESHOLD=8.0
MAX_ITERATIONS=3
```

### 3. 실행 방법

#### CLI에서 실행
```bash
# ADK CLI 사용
adk run mvp_report_generator
```

#### 웹 서버로 실행
```bash
# 웹 서버 시작
chmod +x start_web.sh
./start_web.sh
```

웹 브라우저에서 `http://localhost:8000`에 접속하여 사용할 수 있습니다.

## 📈 사용 예시

### 1. 샘플 데이터로 테스트
```bash
# 웹 인터페이스에서 "샘플 데이터로 리포트 생성" 버튼 클릭
# 또는 CLI에서 직접 실행
adk run mvp_report_generator
```

### 2. CSV 파일 업로드
- 웹 인터페이스에서 CSV 파일 업로드
- 리포트 생성 및 품질 평가 자동 실행
- 생성된 리포트는 `data/reports/` 디렉토리에 저장

### 3. 리포트 확인
- 웹 인터페이스에서 "리포트 목록 보기" 클릭
- 생성된 리포트 파일들을 확인하고 다운로드 가능

## ⚙️ 설정 옵션

### 환경 변수
- `QUALITY_THRESHOLD`: 품질 임계값 (기본값: 8.0)
- `MAX_ITERATIONS`: 최대 반복 횟수 (기본값: 3)
- `GENAI_MODEL`: 사용할 AI 모델 (기본값: gemini-2.0-flash)
- `REPORTS_DIR`: 리포트 저장 디렉토리 (기본값: ./data/reports)

### 품질 평가 기준 조정
`mvp_agent/policy.json` 파일에서 평가 기준과 가중치를 조정할 수 있습니다.

## 🔍 리포트 품질 평가 기준

### 완성도 (30% 가중치)
- 요약 섹션 포함 여부
- 주요 발견사항 섹션 포함 여부
- 데이터 분석 섹션 포함 여부
- 결론 및 권장사항 섹션 포함 여부

### 명확성 (25% 가중치)
- 문장의 명확성과 이해도
- 전문 용어의 적절한 설명
- 데이터 해석의 명확성
- 전체적인 흐름의 논리성

### 정확성 (25% 가중치)
- 데이터 분석의 정확성
- 통계적 계산의 올바름
- 트렌드 분석의 합리성
- 데이터 기반 결론 도출

### 구조 (20% 가중치)
- 섹션 간 연결의 자연스러움
- 정보의 논리적 순서 배치
- 적절한 제목과 부제목 사용
- 전체적인 구조의 일관성

## 🚨 주의사항

1. **Google API 키 필요**: Google Gemini API 키가 필요합니다.
2. **CSV 형식**: 업로드하는 CSV 파일은 한국어 컬럼명을 사용해야 합니다.
3. **메모리 사용량**: 대용량 CSV 파일의 경우 메모리 사용량에 주의하세요.
4. **반복 횟수**: 품질이 낮은 경우 최대 3회까지 반복 실행됩니다.

## 🤝 기여하기

1. 이슈 리포트: 버그나 개선 사항을 이슈로 등록
2. 풀 리퀘스트: 새로운 기능이나 버그 수정 제안
3. 문서 개선: README나 코드 주석 개선

## 📄 라이선스

MIT License

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해 주세요.