import os
from pathlib import Path

# 프로젝트 루트 경로 - 절대 경로로 통일 (mvp 프로젝트 패턴 적용)
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VDATA_DIR = DATA_DIR / "vdata"
REPORTS_DIR = DATA_DIR / "reports"

# 기본 데이터 검증 설정
DEFAULT_REQUIRED_COLUMNS = []  # 동적 분석을 위해 빈 리스트로 설정
DEFAULT_MIN_ROWS = 1

# 에이전트 설정
DEFAULT_MODEL_NAME = "gemini-2.5-flash"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_OUTPUT_TOKENS = 2048