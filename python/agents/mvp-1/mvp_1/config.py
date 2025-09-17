import os
from pathlib import Path

# 환경 변수에서 설정값 로드
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "8.0"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
DEFAULT_MODEL_NAME = "gemini-2.0-flash"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_OUTPUT_TOKENS = 2048
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 프로젝트 루트 경로 - 절대 경로로 통일
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VDATA_DIR = DATA_DIR / "vdata"
REPORTS_DIR = DATA_DIR / "reports"
SAMPLE_DATA_PATH = DATA_DIR / "sample_sales_data.csv"

# 리포트 품질 평가 기준 가중치
QUALITY_WEIGHTS = {
    "completeness": 0.30,  # 완성도 30%
    "clarity": 0.25,       # 명확성 25%
    "accuracy": 0.25,      # 정확성 25%
    "structure": 0.20      # 구조 20%
}

# 리포트 필수 섹션
REQUIRED_SECTIONS = [
    "요약",
    "주요 발견사항",
    "데이터 분석",
    "결론 및 권장사항"
]

# 기본 데이터 검증 설정
DEFAULT_REQUIRED_COLUMNS = []  # 동적 분석을 위해 빈 리스트로 설정
DEFAULT_MIN_ROWS = 1

# 모델 설정 (mvp-1 스타일)
from google.adk.models import Gemini
GENAI_MODEL = Gemini(
    model=DEFAULT_MODEL_NAME,
    temperature=DEFAULT_TEMPERATURE,
    max_output_tokens=DEFAULT_MAX_OUTPUT_TOKENS
)