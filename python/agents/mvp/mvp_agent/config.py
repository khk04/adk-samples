import os
from pathlib import Path

# 환경 변수에서 설정값 로드
QUALITY_THRESHOLD = float(os.getenv("QUALITY_THRESHOLD", "8.0"))
MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "3"))
GENAI_MODEL = os.getenv("GENAI_MODEL", "gemini-1.5-flash")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# 프로젝트 루트 경로 - 절대 경로로 통일
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
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