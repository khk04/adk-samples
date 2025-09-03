#!/bin/bash

# Document Question & Report Agent 통합 배시 스크립트
# 백엔드 API, 프론트엔드, Redis를 함께 실행합니다.

set -e

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 스크립트 정보
SCRIPT_NAME="deploy.sh"
VERSION="1.0.0"

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 헬프 메시지
show_help() {
    cat << EOF
${CYAN}Document Question & Report Agent 통합 배시 스크립트${NC}

사용법: $0 [옵션]

옵션:
    -h, --help          이 도움말을 표시합니다
    -v, --version       버전 정보를 표시합니다
    -b, --build         이미지를 빌드합니다
    -r, --run           서비스를 실행합니다
    -s, --stop          서비스를 중지합니다
    -d, --down          서비스를 완전히 제거합니다
    -l, --logs          로그를 확인합니다
    -t, --test          서비스 상태를 테스트합니다
    -c, --clean         모든 컨테이너와 이미지를 정리합니다
    -f, --full          전체 배포 (빌드 + 실행)
    --status            서비스 상태를 확인합니다

예시:
    $0 --full           # 전체 배포 (빌드 + 실행)
    $0 --run            # 기존 이미지로 서비스 실행
    $0 --stop           # 서비스 중지
    $0 --logs           # 로그 확인

${YELLOW}📋 서비스 구성:${NC}
• 백엔드 API (포트 8000)
• 프론트엔드 (포트 8080)
• Redis (포트 6379)

EOF
}

# 버전 정보
show_version() {
    echo "$SCRIPT_NAME v$VERSION"
    echo "Document Question & Report Agent 통합 배시 스크립트"
}

# Docker 및 Docker Compose 확인
check_dependencies() {
    log_step "의존성 확인 중..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi
    
    log_success "Docker 및 Docker Compose 확인 완료"
}

# 이미지 빌드
build_images() {
    log_step "Docker 이미지 빌드 중..."
    
    # 백엔드 이미지 빌드
    log_info "백엔드 이미지 빌드 중..."
    docker build -t doc-question-report-agent:latest .
    
    # 프론트엔드 이미지 빌드
    log_info "프론트엔드 이미지 빌드 중..."
    docker build -t doc-agent-frontend:latest ./frontend
    
    log_success "모든 이미지 빌드 완료"
}

# 서비스 실행
run_services() {
    log_step "Docker Compose 서비스 실행 중..."
    
    # 환경 변수 파일 확인
    if [ -f ".env" ]; then
        log_info ".env 파일을 사용합니다"
    else
        log_warning ".env 파일이 없습니다. 기본값을 사용합니다"
    fi
    
    # 서비스 실행
    docker-compose up -d
    
    log_success "서비스 실행 완료"
    show_service_info
}

# 서비스 중지
stop_services() {
    log_step "Docker Compose 서비스 중지 중..."
    
    docker-compose stop
    
    log_success "서비스 중지 완료"
}

# 서비스 완전 제거
down_services() {
    log_step "Docker Compose 서비스 완전 제거 중..."
    
    docker-compose down
    
    log_success "서비스 완전 제거 완료"
}

# 로그 확인
show_logs() {
    log_step "서비스 로그 확인 중..."
    
    echo -e "${CYAN}=== 백엔드 로그 ===${NC}"
    docker-compose logs doc-question-report-agent
    
    echo -e "${CYAN}=== 프론트엔드 로그 ===${NC}"
    docker-compose logs doc-agent-frontend
    
    echo -e "${CYAN}=== Redis 로그 ===${NC}"
    docker-compose logs redis
}

# 서비스 상태 테스트
test_services() {
    log_step "서비스 상태 테스트 중..."
    
    # 백엔드 API 테스트
    log_info "백엔드 API 테스트..."
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "백엔드 API 정상 동작"
    else
        log_error "백엔드 API 연결 실패"
        return 1
    fi
    
    # 프론트엔드 테스트
    log_info "프론트엔드 테스트..."
    if curl -s http://localhost:8080 > /dev/null; then
        log_success "프론트엔드 정상 동작"
    else
        log_error "프론트엔드 연결 실패"
        return 1
    fi
    
    # Redis 테스트
    log_info "Redis 테스트..."
    if docker-compose exec redis redis-cli ping | grep -q "PONG"; then
        log_success "Redis 정상 동작"
    else
        log_error "Redis 연결 실패"
        return 1
    fi
    
    log_success "모든 서비스 테스트 통과"
}

# 서비스 정보 표시
show_service_info() {
    cat << EOF

${CYAN}🎉 Document Question & Report Agent 배포 완료!${NC}

${GREEN}📱 프론트엔드:${NC} http://localhost:8080
${GREEN}🔧 백엔드 API:${NC} http://localhost:8000
${GREEN}📚 API 문서:${NC} http://localhost:8000/docs
${GREEN}🗄️  Redis:${NC} localhost:6379

${YELLOW}💡 사용법:${NC}
1. 브라우저에서 http://localhost:8080 접속
2. 문서 업로드 → 질문 생성 → 리포트 생성
3. API 테스트는 http://localhost:8000/docs 에서

${YELLOW}🔍 로그 확인:${NC} $0 --logs
${YELLOW}⏹️  서비스 중지:${NC} $0 --stop
${YELLOW}🗑️  서비스 제거:${NC} $0 --down

EOF
}

# 서비스 상태 확인
show_status() {
    log_step "서비스 상태 확인 중..."
    
    docker-compose ps
    
    echo ""
    log_info "컨테이너 상태:"
    docker ps --filter "name=doc-question-report-agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
}

# 정리 작업
clean_all() {
    log_step "모든 컨테이너와 이미지 정리 중..."
    
    log_warning "이 작업은 모든 컨테이너와 이미지를 삭제합니다. 계속하시겠습니까? (y/N)"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        docker-compose down --rmi all --volumes --remove-orphans
        docker system prune -f
        log_success "정리 작업 완료"
    else
        log_info "정리 작업이 취소되었습니다"
    fi
}

# 메인 함수
main() {
    # 인수가 없으면 도움말 표시
    if [ $# -eq 0 ]; then
        show_help
        exit 0
    fi
    
    # 의존성 확인
    check_dependencies
    
    # 옵션 처리
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -v|--version)
                show_version
                exit 0
                ;;
            -b|--build)
                build_images
                ;;
            -r|--run)
                run_services
                ;;
            -s|--stop)
                stop_services
                ;;
            -d|--down)
                down_services
                ;;
            -l|--logs)
                show_logs
                ;;
            -t|--test)
                test_services
                ;;
            -c|--clean)
                clean_all
                ;;
            -f|--full)
                build_images
                run_services
                ;;
            --status)
                show_status
                ;;
            *)
                log_error "알 수 없는 옵션: $1"
                show_help
                exit 1
                ;;
        esac
        shift
    done
}

# 스크립트 실행
main "$@"