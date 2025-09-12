#!/bin/bash

# MVP Report Generator main.py 직접 실행 스크립트

echo "🚀 MVP Report Generator main.py를 직접 실행합니다..."

# 가상환경 활성화
source .venv/bin/activate

# 필요한 디렉토리 생성
mkdir -p data reports static

# main.py 직접 실행
echo "📊 FastAPI 서버를 시작합니다 (포트 8000)..."
python main.py

