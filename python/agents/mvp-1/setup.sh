#!/bin/bash

echo "MVP-1: 사용자 데이터 기반 질의 생성 에이전트 설정 시작..."

echo "현재 설치된 패키지 확인:"
echo "   - matplotlib: $(pip show matplotlib 2>/dev/null | grep Version | cut -d' ' -f2 || echo '설치되지 않음')"
echo "   - seaborn: $(pip show seaborn 2>/dev/null | grep Version | cut -d' ' -f2 || echo '설치되지 않음')"
echo "   - plotly: $(pip show plotly 2>/dev/null | grep Version | cut -d' ' -f2 || echo '설치되지 않음')"
echo "   - numpy: $(pip show numpy 2>/dev/null | grep Version | cut -d' ' -f2 || echo '설치되지 않음')"
echo "   - pandas: $(pip show pandas 2>/dev/null | grep Version | cut -d' ' -f2 || echo '설치되지 않음')"
echo ""

# 가상환경 생성 및 활성화 (이미 있으면 스킵)
if [ ! -d ".venv" ]; then
    echo "가상환경 생성 중..."
    python3 -m venv .venv
else
    echo "가상환경이 이미 존재합니다."
fi

source .venv/bin/activate
echo "가상환경 활성화 완료"

# Poetry 설치 (이미 있으면 스킵)
if ! command -v poetry &> /dev/null; then
    echo "Poetry 설치 중..."
    pip install poetry
else
    echo "Poetry가 이미 설치되어 있습니다."
fi

# 의존성 설치
echo "의존성 설치 중..."
poetry install --no-root

# 디렉토리 생성
mkdir -p data/reports
mkdir -p tests

echo ""
echo "MVP-1 설정 완료!"
echo "웹 서버 시작: ./start_web.sh"
echo "시각화 기능이 포함된 동적 리포트 생성 에이전트가 준비되었습니다!"
