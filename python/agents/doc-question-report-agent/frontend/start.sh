#!/bin/bash

# Document Question & Report Agent Frontend 실행 스크립트

echo "🚀 Document Question & Report Agent Frontend 시작 중..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Node.js 버전 확인
echo -e "${BLUE}📋 Node.js 버전 확인 중...${NC}"
if ! command -v node &> /dev/null; then
    echo -e "${RED}❌ Node.js가 설치되지 않았습니다.${NC}"
    echo "Node.js 18 이상을 설치해주세요: https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    echo -e "${RED}❌ Node.js 18 이상이 필요합니다. 현재 버전: $(node -v)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Node.js 버전: $(node -v)${NC}"

# npm 버전 확인
echo -e "${BLUE}📋 npm 버전 확인 중...${NC}"
if ! command -v npm &> /dev/null; then
    echo -e "${RED}❌ npm이 설치되지 않았습니다.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ npm 버전: $(npm -v)${NC}"

# 의존성 설치 확인
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}📦 의존성 설치 중...${NC}"
    npm install
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ 의존성 설치에 실패했습니다.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 의존성 설치 완료${NC}"
else
    echo -e "${GREEN}✅ 의존성이 이미 설치되어 있습니다.${NC}"
fi

# 백엔드 API 상태 확인
echo -e "${BLUE}🔍 백엔드 API 상태 확인 중...${NC}"
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 백엔드 API가 실행 중입니다 (localhost:8000)${NC}"
else
    echo -e "${YELLOW}⚠️  백엔드 API에 연결할 수 없습니다.${NC}"
    echo "백엔드 서버가 실행 중인지 확인해주세요:"
    echo "  cd ../ && ./docker-build.sh run"
fi

# 개발 서버 시작
echo -e "${BLUE}🌐 개발 서버 시작 중...${NC}"
echo -e "${GREEN}✅ 프론트엔드가 http://localhost:3000 에서 실행됩니다${NC}"
echo -e "${BLUE}📱 브라우저에서 http://localhost:3000 을 열어주세요${NC}"
echo ""

# Ctrl+C로 종료할 수 있도록 안내
echo -e "${YELLOW}💡 서버를 종료하려면 Ctrl+C를 누르세요${NC}"
echo ""

# 개발 서버 실행
npm run serve