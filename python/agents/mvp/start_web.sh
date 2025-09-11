#!/bin/bash

# MVP Report Generator 웹 서버 시작 스크립트

echo "🌐 MVP Report Generator 웹 서버를 시작합니다..."

source .venv/bin/activate

adk web --host 0.0.0.0 --port 8000
