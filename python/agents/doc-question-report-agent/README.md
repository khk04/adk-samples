# Document Question & Report Agent (ADK)

Google Agent Development Kit (ADK)를 활용한 2-Agent 시스템으로 문서 처리와 질문 응답, 보고서 생성을 수행하는 AI 에이전트입니다.

## 🏗️ 아키텍처

```
┌─────────────────────┐    ┌─────────────────────┐
│  Document &         │    │     Report          │
│  Question Agent     │◄──►│      Agent          │
│  (ADK Agent)        │    │   (ADK Agent)       │
│                     │    │                     │
│ • 문서 분석         │    │ • 보고서 생성       │
│ • 질문 이해         │    │ • 데이터 시각화     │
│ • 정보 추출         │    │ • 포맷 변환         │
│ • 컨텍스트 관리     │    │ • 출력 최적화       │
└─────────────────────┘    └─────────────────────┘
            │                        │
            └────────┬─────────────────┘
                     │
            ┌─────────────────────┐
            │   Main Coordinator  │
            │      Agent          │
            │   (ADK LlmAgent)    │
            │                     │
            │ • 에이전트 조율     │
            │ • 워크플로우 관리   │
            │ • 사용자 상호작용   │
            └─────────────────────┘
```

## 🚀 주요 기능

### Document & Question Agent (ADK Agent)
- **문서 분석**: 다양한 형식 지원 (PDF, DOCX, TXT, HTML, CSV, Excel)
- **질문 생성**: 단계별 질문 후보 생성 및 후속 질문 생성
- **컨텍스트 관리**: 문서 내용 기반 컨텍스트 추출 및 관리
- **MCP 도구 활용**: 문서 처리 및 분석을 위한 전용 도구들

### Report Agent (ADK Agent)
- **보고서 생성**: 분석 결과를 바탕으로 구조화된 보고서 생성
- **데이터 시각화**: 차트, 그래프, 인포그래픽 포함
- **다양한 출력 형식**: PDF, HTML, DOCX, PPTX 지원
- **피드백 반영**: 사용자 피드백을 통한 보고서 개선

### Main Coordinator Agent (ADK LlmAgent)
- **에이전트 조율**: Document Question Agent와 Report Agent 간의 협업 관리
- **워크플로우 관리**: 문서 분석 → 질문 생성 → 보고서 생성 프로세스 관리
- **사용자 상호작용**: 자연어 기반 사용자 요청 처리

## 📋 사전 요구사항

- Python 3.9+
- Google Cloud Platform 계정
- Google ADK 설치

## 🛠️ 설치 및 실행

### 1. 저장소 클론
```bash
git clone https://github.com/yourusername/doc-question-report-agent.git
cd doc-question-report-agent
```

### 2. 환경 설정
```bash
# 환경 변수 파일 생성
cp .env.example .env

# Google Cloud 인증 설정
gcloud auth application-default login
```

### 3. 의존성 설치
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate     # Windows

# 의존성 설치
pip install -e .
```

### 4. 실행
```bash
# 메인 시스템 실행
python -m doc_question_report_agent.main

# 또는 직접 실행
python doc_question_report_agent/main.py
```

## 🎮 사용법

### 기본 사용법

```python
from doc_question_report_agent import system

# 시스템 초기화
system = DocQuestionReportSystem()

# 사용자 요청 처리
response = await system.process_user_request(
    "문서를 분석하고 질문을 생성해주세요."
)

# 문서 분석
result = await system.analyze_document(
    file_path="/path/to/document.pdf",
    filename="document.pdf"
)

# 질문 생성
questions = await system.generate_questions(
    document_id="doc_123",
    step=1
)

# 보고서 생성
report = await system.generate_report(
    title="분석 보고서",
    report_type="executive_summary",
    document_id="doc_123",
    selected_questions=["질문1", "질문2"]
)
```

### ADK 에이전트 직접 사용

```python
from doc_question_report_agent import (
    root_agent,
    document_question_agent,
    report_agent
)

# 메인 에이전트 사용
response = await root_agent.run("문서를 분석해주세요.")

# Document Question Agent 사용
response = await document_question_agent.run(
    "이 문서에 대해 질문을 생성해주세요.",
    context={"document_id": "doc_123"}
)

# Report Agent 사용
response = await report_agent.run(
    "분석 보고서를 생성해주세요.",
    context={"title": "보고서", "document_id": "doc_123"}
)
```

## 🔧 개발

### 프로젝트 구조

```
doc-question-report-agent/
├── doc_question_report_agent/     # 메인 패키지
│   ├── agents.py                  # ADK 에이전트 클래스
│   ├── main.py                    # 메인 시스템 클래스
│   ├── models.py                  # 데이터 모델
│   ├── tools.py                   # MCP 도구들
│   ├── prompt.py                  # 에이전트 지시사항
│   └── utils.py                   # 유틸리티 함수
├── frontend/                      # Vue.js 프론트엔드
├── docker-compose.yml             # Docker Compose 설정
├── pyproject.toml                 # Python 프로젝트 설정
└── README.md
```

### 테스트 실행

```bash
# 단위 테스트
pytest tests/

# 통합 테스트
pytest tests/ -m integration
```

## 🛠️ MCP 도구들

이 시스템은 다음과 같은 MCP 도구들을 제공합니다:

- `analyze_document`: 문서 분석 및 텍스트 추출
- `generate_questions`: 질문 후보 생성
- `regenerate_questions`: 후속 질문 생성
- `generate_report_draft`: 보고서 초안 생성
- `finalize_report`: 최종 보고서 완성
- `get_document_status`: 문서 처리 상태 조회
- `list_available_documents`: 사용 가능한 문서 목록
- `export_report_to_pdf`: PDF 형식으로 보고서 내보내기

## 🔐 보안

- Google Cloud Platform 보안 정책 준수
- 문서 업로드 크기 제한
- 허용된 파일 형식만 처리
- 컨테이너 기반 격리된 실행 환경

## 📊 모니터링

- 시스템 상태 조회: `await system.get_system_status()`
- 문서 처리 상태: `get_document_status(document_id)`
- 사용 가능한 문서 목록: `list_available_documents()`

## 🤝 기여

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

Apache License 2.0

## 🆘 문제 해결

### 일반적인 문제

1. **Google Cloud 인증 오류**
   ```bash
   gcloud auth application-default login
   ```

2. **ADK 설치 오류**
   ```bash
   pip install google-adk>=1.3.0
   ```

3. **의존성 충돌**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

## 📞 지원

- GitHub Issues: [문제 보고](https://github.com/yourusername/doc-question-report-agent/issues)
- Google Cloud Support: [Google Cloud 지원](https://cloud.google.com/support)