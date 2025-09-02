#!/bin/bash

# DocQuestionReport Agent Docker 빌드 스크립트
# 사용법: ./docker-build.sh [build|run|test|clean|all]

set -e  # 오류 발생 시 스크립트 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 변수 정의
IMAGE_NAME="doc-question-report-agent"
IMAGE_TAG="latest"
CONTAINER_NAME="doc-question-report-agent-container"
PORT=8000
VOLUME_PATH="$(pwd)/output:/app/output"
NETWORK_NAME="doc-question-network"

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

# 도움말 출력
show_help() {
    echo "DocQuestionReport Agent Docker 빌드 스크립트"
    echo ""
    echo "사용법: $0 [COMMAND]"
    echo ""
    echo "COMMANDS:"
    echo "  build     - Docker 이미지 빌드"
    echo "  run       - 컨테이너 실행"
    echo "  test      - 컨테이너 테스트"
    echo "  stop      - 컨테이너 중지"
    echo "  clean     - 이미지 및 컨테이너 정리"
    echo "  logs      - 컨테이너 로그 확인"
    echo "  shell     - 컨테이너 내부 접속"
    echo "  all       - 빌드, 실행, 테스트 전체 과정"
    echo "  help      - 이 도움말 출력"
    echo ""
    echo "예시:"
    echo "  $0 build    # 이미지 빌드"
    echo "  $0 all      # 전체 과정 실행"
}

# Docker 설치 확인
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker가 설치되지 않았습니다. Docker를 먼저 설치해주세요."
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        log_error "Docker 데몬이 실행되지 않았습니다. Docker를 시작해주세요."
        exit 1
    fi
    
    log_success "Docker 확인 완료"
}

# 네트워크 생성
create_network() {
    if ! docker network ls | grep -q "$NETWORK_NAME"; then
        log_info "Docker 네트워크 생성: $NETWORK_NAME"
        docker network create "$NETWORK_NAME"
    else
        log_info "Docker 네트워크가 이미 존재합니다: $NETWORK_NAME"
    fi
}

# 이미지 빌드
build_image() {
    log_info "Docker 이미지 빌드 시작..."
    
    # 빌드 컨텍스트 확인
    if [ ! -f "Dockerfile" ]; then
        log_error "Dockerfile을 찾을 수 없습니다. 올바른 디렉토리에서 실행해주세요."
        exit 1
    fi
    
    # .dockerignore 파일 생성 (없는 경우)
    if [ ! -f ".dockerignore" ]; then
        log_info ".dockerignore 파일 생성"
        cat > .dockerignore << EOF
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env
pip-log.txt
pip-delete-this-directory.txt
.tox
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.mypy_cache
.pytest_cache
.hypothesis
.DS_Store
*.swp
*.swo
*~
EOF
    fi
    
    # 이미지 빌드
    docker build -t "$IMAGE_NAME:$IMAGE_TAG" . \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --progress=plain
    
    if [ $? -eq 0 ]; then
        log_success "Docker 이미지 빌드 완료: $IMAGE_NAME:$IMAGE_TAG"
        
        # 이미지 정보 출력
        log_info "빌드된 이미지 정보:"
        docker images "$IMAGE_NAME:$IMAGE_TAG"
    else
        log_error "Docker 이미지 빌드 실패"
        exit 1
    fi
}

# 컨테이너 실행
run_container() {
    log_info "컨테이너 실행 시작..."
    
    # 기존 컨테이너가 실행 중인지 확인
    if docker ps | grep -q "$CONTAINER_NAME"; then
        log_warning "컨테이너가 이미 실행 중입니다: $CONTAINER_NAME"
        log_info "기존 컨테이너를 중지하고 새로 시작합니다."
        stop_container
    fi
    
    # 기존 컨테이너가 존재하는지 확인
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        log_info "기존 컨테이너 제거: $CONTAINER_NAME"
        docker rm "$CONTAINER_NAME"
    fi
    
    # 출력 디렉토리 생성
    mkdir -p output
    
    # 컨테이너 실행
    docker run -d \
        --name "$CONTAINER_NAME" \
        --network "$NETWORK_NAME" \
        -p "$PORT:8000" \
        -v "$VOLUME_PATH" \
        -e PYTHONUNBUFFERED=1 \
        -e LOG_LEVEL=INFO \
        --restart unless-stopped \
        "$IMAGE_NAME:$IMAGE_TAG"
    
    if [ $? -eq 0 ]; then
        log_success "컨테이너 실행 완료: $CONTAINER_NAME"
        log_info "포트: $PORT"
        log_info "볼륨: $VOLUME_PATH"
        
        # 컨테이너 상태 확인
        sleep 3
        docker ps | grep "$CONTAINER_NAME"
    else
        log_error "컨테이너 실행 실패"
        exit 1
    fi
}

# 컨테이너 테스트
test_container() {
    log_info "컨테이너 테스트 시작..."
    
    # 컨테이너가 실행 중인지 확인
    if ! docker ps | grep -q "$CONTAINER_NAME"; then
        log_error "컨테이너가 실행되지 않았습니다. 먼저 실행해주세요."
        exit 1
    fi
    
    # 헬스체크
    log_info "헬스체크 수행..."
    for i in {1..10}; do
        if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
            log_success "헬스체크 성공 (시도: $i)"
            break
        elif [ $i -eq 10 ]; then
            log_error "헬스체크 실패 (10회 시도 후)"
            exit 1
        else
            log_info "헬스체크 대기 중... (시도: $i/10)"
            sleep 2
        fi
    done
    
    # API 엔드포인트 테스트
    log_info "API 엔드포인트 테스트..."
    
    # 상태 확인
    if curl -s "http://localhost:$PORT/status" > /dev/null 2>&1; then
        log_success "상태 확인 API 테스트 성공"
    else
        log_warning "상태 확인 API 테스트 실패"
    fi
    
    # 컨테이너 로그 확인
    log_info "최근 컨테이너 로그:"
    docker logs --tail 20 "$CONTAINER_NAME"
    
    log_success "컨테이너 테스트 완료"
}

# 컨테이너 중지
stop_container() {
    log_info "컨테이너 중지..."
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        docker stop "$CONTAINER_NAME"
        log_success "컨테이너 중지 완료: $CONTAINER_NAME"
    else
        log_info "실행 중인 컨테이너가 없습니다: $CONTAINER_NAME"
    fi
}

# 컨테이너 로그 확인
show_logs() {
    log_info "컨테이너 로그 확인..."
    
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        docker logs -f "$CONTAINER_NAME"
    else
        log_error "컨테이너를 찾을 수 없습니다: $CONTAINER_NAME"
        exit 1
    fi
}

# 컨테이너 내부 접속
access_shell() {
    log_info "컨테이너 내부 접속..."
    
    if docker ps | grep -q "$CONTAINER_NAME"; then
        docker exec -it "$CONTAINER_NAME" /bin/bash
    else
        log_error "컨테이너가 실행되지 않았습니다. 먼저 실행해주세요."
        exit 1
    fi
}

# 정리 작업
clean_all() {
    log_info "Docker 리소스 정리 시작..."
    
    # 컨테이너 중지 및 제거
    if docker ps -a | grep -q "$CONTAINER_NAME"; then
        log_info "컨테이너 제거: $CONTAINER_NAME"
        docker stop "$CONTAINER_NAME" 2>/dev/null || true
        docker rm "$CONTAINER_NAME" 2>/dev/null || true
    fi
    
    # 이미지 제거
    if docker images | grep -q "$IMAGE_NAME"; then
        log_info "이미지 제거: $IMAGE_NAME:$IMAGE_TAG"
        docker rmi "$IMAGE_NAME:$IMAGE_TAG" 2>/dev/null || true
    fi
    
    # 네트워크 제거
    if docker network ls | grep -q "$NETWORK_NAME"; then
        log_info "네트워크 제거: $NETWORK_NAME"
        docker network rm "$NETWORK_NAME" 2>/dev/null || true
    fi
    
    # 출력 디렉토리 정리 (선택사항)
    read -p "출력 디렉토리도 정리하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "출력 디렉토리 정리"
        rm -rf output/*
    fi
    
    log_success "Docker 리소스 정리 완료"
}

# 전체 과정 실행
run_all() {
    log_info "전체 과정 실행 시작..."
    
    check_docker
    create_network
    build_image
    run_container
    test_container
    
    log_success "전체 과정 완료!"
    log_info "애플리케이션 접속: http://localhost:$PORT"
}

# 메인 로직
main() {
    case "${1:-help}" in
        "build")
            check_docker
            build_image
            ;;
        "run")
            check_docker
            create_network
            run_container
            ;;
        "test")
            test_container
            ;;
        "stop")
            stop_container
            ;;
        "clean")
            clean_all
            ;;
        "logs")
            show_logs
            ;;
        "shell")
            access_shell
            ;;
        "all")
            run_all
            ;;
        "help"|*)
            show_help
            ;;
    esac
}

# 스크립트 실행
main "$@"