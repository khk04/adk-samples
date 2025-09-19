#!/bin/bash

# MVP-1: 사용자 데이터 기반 질의 생성 에이전트 웹 서버 시작 스크립트

echo "🌐 MVP-1: 사용자 데이터 기반 질의 생성 에이전트 웹 서버를 시작합니다..."

source .venv/bin/activate

adk web --host 0.0.0.0 --port 8000 --reload
