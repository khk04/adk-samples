#!/bin/bash

# MVP Report Generator 초기 설정 스크립트

echo "🚀 MVP Report Generator 초기 설정을 시작합니다..."

# python 가상환경 생가
python3 -m venv .venv
source .venv/bin/activate

# Poetry 설치 확인
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry가 설치되어 있지 않습니다."
    echo "다음 명령어로 Poetry를 설치하세요:"
    echo "curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

echo "✅ Poetry 확인 완료"

# 환경 변수 파일 설정
if [ ! -f .env ]; then
    echo "📝 .env 파일을 생성합니다..."
    cp .env.example .env
    echo "⚠️  .env 파일을 편집하여 Google API 키를 설정하세요."
else
    echo "✅ .env 파일이 이미 존재합니다."
fi

# 의존성 설치
echo "📦 의존성을 설치합니다..."
poetry install

# 리포트 디렉토리 생성
echo "📁 리포트 디렉토리를 생성합니다..."
mkdir -p data/reports

echo "🎉 초기 설정이 완료되었습니다!"
echo ""
echo "다음 단계:"
echo "1. .env 파일을 편집하여 Google API 키를 설정하세요"
echo "2. 'poetry run python start_web.sh' 명령어로 웹 서버를 시작하세요"
echo "3. 또는 'adk run mvp_report_generator' 명령어로 CLI에서 실행하세요"