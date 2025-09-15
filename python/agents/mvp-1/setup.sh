#!/bin/bash

echo "🚀 MVP-1: 사용자 데이터 기반 질의 생성 에이전트 설정 시작..."

# 가상환경 생성 및 활성화
python3 -m venv .venv
source .venv/bin/activate

# Poetry 설치 및 의존성 설치
pip install poetry
poetry install --no-root

# 디렉토리 생성
mkdir -p data/reports
