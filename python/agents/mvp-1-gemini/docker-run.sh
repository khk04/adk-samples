#!/bin/bash

# MVP-1 Gemini Docker 실행 스크립트
# 작성자: AI Assistant
# 설명: Docker Compose를 사용하여 MVP-1 Gemini 애플리케이션을 빌드하고 실행

set -e  # 에러 발생 시 스크립트 종료

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수들
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

# 스크립트 사용법 출력
usage() {
    echo "사용법: $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  build       Docker 이미지만 빌드"
    echo "  up          컨테이너 실행"
    echo "  down        컨테이너 중지 및 제거"
    echo "  restart     컨테이너 재시작"
    echo "  logs        로그 확인"
    echo "  clean       사용하지 않는 이미지 및 컨테이너 정리"
    echo "  status      컨테이너 상태 확인"
    echo "  health      헬스체크 확인"
    echo "  help        이 도움말 표시"
    echo ""
    echo "예시:"
    echo "  $0 build    # 이미지 빌드"
    echo "  $0 up       # 애플리케이션 실행"
    echo "  $0 logs     # 로그 확인"
}

# 환경 변수 파일 확인
check_env_file() {
    if [ ! -f ".env" ]; then
        log_warning ".env 파일이 없습니다. .env.example을 복사하여 생성합니다."
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_success ".env 파일이 생성되었습니다."
            log_warning "Google API 키를 설정한 후 다시 실행해주세요."
            exit 1
        else
            log_error ".env.example 파일이 없습니다."
            exit 1
        fi
    fi
}

# Docker 설치 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다."
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose가 설치되지 않았습니다."
        exit 1
    fi

    # Docker 데몬 실행 확인
    if ! docker info &> /dev/null; then
        log_error "Docker 데몬이 실행되지 않았습니다. Docker를 시작해주세요."
        exit 1
    fi
}

# 필요한 디렉토리 생성
create_directories() {
    log_info "필요한 디렉토리를 생성합니다..."
    mkdir -p data/vdata
    mkdir -p logs
    log_success "디렉토리 생성 완료"
}

# Docker 이미지 빌드
build_images() {
    log_info "Docker 이미지를 빌드합니다..."
    docker-compose build --no-cache
    log_success "이미지 빌드 완료"
}

# 컨테이너 실행
start_containers() {
    log_info "컨테이너를 실행합니다..."
    docker-compose up -d
    log_success "컨테이너 실행 완료"
    
    # 헬스체크 대기
    log_info "서비스 시작을 기다립니다..."
    sleep 10
    
    # 서비스 상태 확인
    if check_health; then
        log_success "모든 서비스가 정상적으로 실행되었습니다!"
        echo ""
        echo "🌐 접속 정보:"
        echo "  프론트엔드: http://localhost:5173"
        echo "  백엔드 API: http://localhost:8000"
        echo "  API 문서: http://localhost:8000/docs"
    else
        log_warning "일부 서비스가 아직 준비되지 않았습니다. 잠시 후 다시 확인해주세요."
    fi
}

# 컨테이너 중지 및 제거
stop_containers() {
    log_info "컨테이너를 중지하고 제거합니다..."
    docker-compose down
    log_success "컨테이너 중지 및 제거 완료"
}

# 컨테이너 재시작
restart_containers() {
    log_info "컨테이너를 재시작합니다..."
    docker-compose restart
    log_success "컨테이너 재시작 완료"
}

# 로그 확인
show_logs() {
    log_info "컨테이너 로그를 확인합니다..."
    docker-compose logs -f
}

# 컨테이너 상태 확인
show_status() {
    log_info "컨테이너 상태를 확인합니다..."
    docker-compose ps
}

# 헬스체크 확인
check_health() {
    local backend_healthy=false
    local frontend_healthy=false
    
    # 백엔드 헬스체크
    if curl -f http://localhost:8000/health &> /dev/null; then
        backend_healthy=true
        log_success "백엔드 서비스가 정상입니다."
    else
        log_warning "백엔드 서비스가 아직 준비되지 않았습니다."
    fi
    
    # 프론트엔드 헬스체크
    if curl -f http://localhost:5173 &> /dev/null; then
        frontend_healthy=true
        log_success "프론트엔드 서비스가 정상입니다."
    else
        log_warning "프론트엔드 서비스가 아직 준비되지 않았습니다."
    fi
    
    if [ "$backend_healthy" = true ] && [ "$frontend_healthy" = true ]; then
        return 0
    else
        return 1
    fi
}

# 정리 작업
clean_up() {
    log_info "사용하지 않는 Docker 리소스를 정리합니다..."
    
    # 중지된 컨테이너 제거
    docker-compose down --remove-orphans
    
    # 사용하지 않는 이미지 제거
    docker image prune -f
    
    # 사용하지 않는 볼륨 제거
    docker volume prune -f
    
    log_success "정리 작업 완료"
}

# 메인 함수
main() {
    case "${1:-help}" in
        "build")
            check_docker
            create_directories
            build_images
            ;;
        "up")
            check_docker
            check_env_file
            create_directories
            start_containers
            ;;
        "down")
            check_docker
            stop_containers
            ;;
        "restart")
            check_docker
            restart_containers
            ;;
        "logs")
            check_docker
            show_logs
            ;;
        "status")
            check_docker
            show_status
            ;;
        "health")
            check_health
            ;;
        "clean")
            check_docker
            clean_up
            ;;
        "help"|*)
            usage
            ;;
    esac
}

# 스크립트 실행
main "$@"
