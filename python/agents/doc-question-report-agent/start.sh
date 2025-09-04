#!/bin/bash

# Document Question & Report Agent 관리 스크립트
# 사용법: ./start.sh [명령어]

set -e

# 색상 정의 (더 호환성 있는 방식)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 프로젝트 정보
PROJECT_NAME="doc-question-report-agent"
COMPOSE_FILE="docker-compose.yml"

# 로고 출력
print_logo() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║    Document Question & Report Agent                         ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 도움말 출력
show_help() {
    print_logo
    echo -e "${YELLOW}사용법: $0 [명령어]${NC}"
    echo ""
    echo -e "${GREEN}사용 가능한 명령어:${NC}"
    echo -e "  ${CYAN}start${NC}     - 서비스 시작 (빌드 포함)"
    echo -e "  ${CYAN}stop${NC}      - 서비스 중지"
    echo -e "  ${CYAN}restart${NC}   - 서비스 재시작"
    echo -e "  ${CYAN}build${NC}     - 이미지 빌드"
    echo -e "  ${CYAN}logs${NC}      - 로그 확인"
    echo -e "  ${CYAN}status${NC}    - 서비스 상태 확인"
    echo -e "  ${CYAN}clean${NC}     - 컨테이너 및 이미지 정리"
    echo -e "  ${CYAN}clean-all${NC} - 모든 데이터 정리 (볼륨 포함)"
    echo -e "  ${CYAN}shell${NC}     - 백엔드 컨테이너 쉘 접속"
    echo -e "  ${CYAN}help${NC}      - 이 도움말 표시"
    echo ""
    echo -e "${YELLOW}예시:${NC}"
    echo -e "  $0 start    # 서비스 시작"
    echo -e "  $0 logs     # 로그 확인"
    echo -e "  $0 stop     # 서비스 중지"
}

# 환경 확인
check_environment() {
    echo -e "${BLUE}🔍 환경 확인 중...${NC}"
    
    # Docker 확인
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker가 설치되지 않았습니다.${NC}"
        exit 1
    fi
    
    # Docker Compose 확인
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose가 설치되지 않았습니다.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 환경 확인 완료${NC}"
}

# 서비스 시작
start_services() {
    print_logo
    check_environment
    
    echo -e "${BLUE}🚀 서비스 시작 중...${NC}"
    
    # Docker Compose로 서비스 시작 (볼륨 자동 생성)
    docker-compose -f $COMPOSE_FILE up -d --build
    
    echo -e "${GREEN}✅ 서비스가 시작되었습니다!${NC}"
    echo ""
    echo -e "${CYAN}📋 서비스 정보:${NC}"
    echo "  • 백엔드 API: http://localhost:8000"
    echo "  • 프론트엔드: http://localhost:8080"
    echo ""
    echo -e "${CYAN}📁 데이터 볼륨:${NC}"
    echo "  • 업로드 파일: Docker 볼륨 'uploads'"
    echo "  • 생성된 리포트: Docker 볼륨 'output'"
    echo "  • 임시 파일: Docker 볼륨 'temp'"
    echo "  • 로그 파일: Docker 볼륨 'logs'"
    echo ""
    echo -e "${YELLOW}💡 유용한 명령어:${NC}"
    echo -e "  $0 logs     # 로그 확인"
    echo -e "  $0 status   # 상태 확인"
    echo -e "  $0 stop     # 서비스 중지"
}

# 서비스 중지
stop_services() {
    echo -e "${BLUE}🛑 서비스 중지 중...${NC}"
    
    docker-compose -f $COMPOSE_FILE down
    
    echo -e "${GREEN}✅ 서비스가 중지되었습니다.${NC}"
}

# 서비스 재시작
restart_services() {
    echo -e "${BLUE}🔄 서비스 재시작 중...${NC}"
    
    docker-compose -f $COMPOSE_FILE restart
    
    echo -e "${GREEN}✅ 서비스가 재시작되었습니다.${NC}"
}

# 이미지 빌드
build_images() {
    echo -e "${BLUE}🔨 이미지 빌드 중...${NC}"
    
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    echo -e "${GREEN}✅ 이미지 빌드가 완료되었습니다.${NC}"
}

# 로그 확인
show_logs() {
    echo -e "${BLUE}📋 로그 확인 중...${NC}"
    echo -e "${YELLOW}Ctrl+C를 눌러 로그 보기를 종료하세요.${NC}"
    echo ""
    
    docker-compose -f $COMPOSE_FILE logs -f
}

# 서비스 상태 확인
show_status() {
    echo -e "${BLUE}📊 서비스 상태 확인 중...${NC}"
    echo ""
    
    # Docker Compose 서비스 상태
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    echo -e "${CYAN}🌐 서비스 엔드포인트:${NC}"
    echo "  • 백엔드 API: http://localhost:8000"
    echo "  • 프론트엔드: http://localhost:8080"
    echo "  • 상태 확인: http://localhost:8000/status"
    
    echo ""
    echo -e "${CYAN}📈 리소스 사용량:${NC}"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}" \
        $(docker-compose -f $COMPOSE_FILE ps -q)
    
    echo ""
    echo -e "${CYAN}💾 볼륨 정보:${NC}"
    docker volume ls | grep $PROJECT_NAME
}

# 정리 (컨테이너 및 이미지)
clean_containers() {
    echo -e "${BLUE}🧹 컨테이너 및 이미지 정리 중...${NC}"
    
    # 서비스 중지
    docker-compose -f $COMPOSE_FILE down
    
    # 사용하지 않는 이미지 삭제
    docker image prune -f
    
    # 프로젝트 관련 이미지 삭제
    docker images | grep $PROJECT_NAME | awk '{print $3}' | xargs -r docker rmi -f
    
    echo -e "${GREEN}✅ 정리가 완료되었습니다.${NC}"
}

# 전체 정리 (볼륨 포함)
clean_all() {
    echo -e "${BLUE}🧹 전체 정리 중 (볼륨 포함)...${NC}"
    
    # 서비스 중지 및 볼륨 삭제
    docker-compose -f $COMPOSE_FILE down -v
    
    # 사용하지 않는 모든 리소스 삭제
    docker system prune -af
    
    echo -e "${GREEN}✅ 전체 정리가 완료되었습니다.${NC}"
}

# 백엔드 컨테이너 쉘 접속
access_shell() {
    echo -e "${BLUE}🐚 백엔드 컨테이너 쉘 접속 중...${NC}"
    
    docker-compose -f $COMPOSE_FILE exec doc-question-report-agent /bin/bash
}

# 메인 로직
main() {
    case "${1:-help}" in
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        build)
            build_images
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            clean_containers
            ;;
        clean-all)
            clean_all
            ;;
        shell)
            access_shell
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo -e "${RED}❌ 알 수 없는 명령어: $1${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# 스크립트 실행
main "$@"