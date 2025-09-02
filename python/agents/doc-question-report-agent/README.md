# Document & Question + Report Agent

2-Agent 시스템으로 문서 처리와 질문 응답, 보고서 생성을 수행하는 AI 에이전트입니다.

## 아키텍처

```
┌─────────────────────┐    ┌─────────────────────┐
│  Document &         │    │     Report          │
│  Question Agent     │◄──►│      Agent          │
│                     │    │                     │
│ • 문서 분석         │    │ • 보고서 생성       │
│ • 질문 이해         │    │ • 데이터 시각화     │
│ • 정보 추출         │    │ • 포맷 변환         │
│ • 컨텍스트 관리     │    │ • 출력 최적화       │
└─────────────────────┘    └─────────────────────┘
```

## 주요 기능

### Document & Question Agent
- 다양한 문서 형식 지원 (PDF, DOCX, TXT, HTML 등)
- 문서 내용 분석 및 구조화
- 사용자 질문 이해 및 컨텍스트 매칭
- 관련 정보 추출 및 요약
- 질문-답변 쌍 생성

### Report Agent
- 분석 결과를 바탕으로 보고서 생성
- 데이터 시각화 (차트, 그래프)
- 다양한 출력 형식 지원 (PDF, HTML, DOCX, PPTX)
- 템플릿 기반 보고서 생성
- 품질 검증 및 최적화

## 설치 및 실행

### 의존성 설치
```bash
pip install -e .
```

### 환경 변수 설정
```bash
cp .env.example .env
# OpenAI API 키 등 필요한 설정 입력
```

### 실행
```bash
python -m doc_question_report_agent.main
```

## 사용 예시

```python
from doc_question_report_agent import DocQuestionReportSystem

# 시스템 초기화
system = DocQuestionReportSystem()

# 문서 업로드 및 분석
doc_analysis = system.analyze_document("document.pdf")

# 질문에 대한 답변 생성
answer = system.answer_question("문서의 주요 내용은 무엇인가요?")

# 보고서 생성
report = system.generate_report(
    title="분석 보고서",
    content=doc_analysis,
    format="pdf"
)
```

## API 엔드포인트

- `POST /analyze` - 문서 분석
- `POST /question` - 질문 응답
- `POST /report` - 보고서 생성
- `GET /status` - 시스템 상태 확인

## 개발

### 테스트 실행
```bash
pytest
```

### 코드 포맷팅
```bash
black .
isort .
```

### 타입 체크
```bash
mypy .
```

## 라이선스

MIT License