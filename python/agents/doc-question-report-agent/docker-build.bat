@echo off
REM DocQuestionReport Agent Docker 빌드 스크립트 (Windows)
REM 사용법: docker-build.bat [build|run|test|clean|all]

setlocal enabledelayedexpansion

REM 색상 정의 (Windows 10 이상)
set "RED=[91m"
set "GREEN=[92m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM 변수 정의
set "IMAGE_NAME=doc-question-report-agent"
set "IMAGE_TAG=latest"
set "CONTAINER_NAME=doc-question-report-agent-container"
set "PORT=8000"
set "VOLUME_PATH=%cd%\output:/app/output"
set "NETWORK_NAME=doc-question-network"

REM 로그 함수
:log_info
echo %BLUE%[INFO]%NC% %~1
goto :eof

:log_success
echo %GREEN%[SUCCESS]%NC% %~1
goto :eof

:log_warning
echo %YELLOW%[WARNING]%NC% %~1
goto :eof

:log_error
echo %RED%[ERROR]%NC% %~1
goto :eof

REM 도움말 출력
:show_help
echo DocQuestionReport Agent Docker 빌드 스크립트 (Windows)
echo.
echo 사용법: %0 [COMMAND]
echo.
echo COMMANDS:
echo   build     - Docker 이미지 빌드
echo   run       - 컨테이너 실행
echo   test      - 컨테이너 테스트
echo   stop      - 컨테이너 중지
echo   clean     - 이미지 및 컨테이너 정리
echo   logs      - 컨테이너 로그 확인
echo   shell     - 컨테이너 내부 접속
echo   all       - 빌드, 실행, 테스트 전체 과정
echo   help      - 이 도움말 출력
echo.
echo 예시:
echo   %0 build    # 이미지 빌드
echo   %0 all      # 전체 과정 실행
goto :eof

REM Docker 설치 확인
:check_docker
docker --version >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker가 설치되지 않았습니다. Docker를 먼저 설치해주세요."
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    call :log_error "Docker 데몬이 실행되지 않았습니다. Docker를 시작해주세요."
    exit /b 1
)

call :log_success "Docker 확인 완료"
goto :eof

REM 네트워크 생성
:create_network
docker network ls | findstr "%NETWORK_NAME%" >nul 2>&1
if errorlevel 1 (
    call :log_info "Docker 네트워크 생성: %NETWORK_NAME%"
    docker network create "%NETWORK_NAME%"
) else (
    call :log_info "Docker 네트워크가 이미 존재합니다: %NETWORK_NAME%"
)
goto :eof

REM 이미지 빌드
:build_image
call :log_info "Docker 이미지 빌드 시작..."

REM 빌드 컨텍스트 확인
if not exist "Dockerfile" (
    call :log_error "Dockerfile을 찾을 수 없습니다. 올바른 디렉토리에서 실행해주세요."
    exit /b 1
)

REM .dockerignore 파일 생성 (없는 경우)
if not exist ".dockerignore" (
    call :log_info ".dockerignore 파일 생성"
    (
        echo __pycache__
        echo *.pyc
        echo *.pyo
        echo *.pyd
        echo .Python
        echo env
        echo pip-log.txt
        echo pip-delete-this-directory.txt
        echo .tox
        echo .coverage
        echo .coverage.*
        echo .cache
        echo nosetests.xml
        echo coverage.xml
        echo *.cover
        echo *.log
        echo .git
        echo .mypy_cache
        echo .pytest_cache
        echo .hypothesis
        echo .DS_Store
        echo *.swp
        echo *.swo
        echo *~
    ) > .dockerignore
)

REM 이미지 빌드
docker build -t "%IMAGE_NAME%:%IMAGE_TAG%" . --build-arg BUILDKIT_INLINE_CACHE=1 --progress=plain

if errorlevel 1 (
    call :log_error "Docker 이미지 빌드 실패"
    exit /b 1
) else (
    call :log_success "Docker 이미지 빌드 완료: %IMAGE_NAME%:%IMAGE_TAG%"
    call :log_info "빌드된 이미지 정보:"
    docker images "%IMAGE_NAME%:%IMAGE_TAG%"
)
goto :eof

REM 컨테이너 실행
:run_container
call :log_info "컨테이너 실행 시작..."

REM 기존 컨테이너가 실행 중인지 확인
docker ps | findstr "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    call :log_warning "컨테이너가 이미 실행 중입니다: %CONTAINER_NAME%"
    call :log_info "기존 컨테이너를 중지하고 새로 시작합니다."
    call :stop_container
)

REM 기존 컨테이너가 존재하는지 확인
docker ps -a | findstr "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    call :log_info "기존 컨테이너 제거: %CONTAINER_NAME%"
    docker rm "%CONTAINER_NAME%"
)

REM 출력 디렉토리 생성
if not exist "output" mkdir output

REM 컨테이너 실행
docker run -d --name "%CONTAINER_NAME%" --network "%NETWORK_NAME%" -p %PORT%:8000 -v "%VOLUME_PATH%" -e PYTHONUNBUFFERED=1 -e LOG_LEVEL=INFO --restart unless-stopped "%IMAGE_NAME%:%IMAGE_TAG%"

if errorlevel 1 (
    call :log_error "컨테이너 실행 실패"
    exit /b 1
) else (
    call :log_success "컨테이너 실행 완료: %CONTAINER_NAME%"
    call :log_info "포트: %PORT%"
    call :log_info "볼륨: %VOLUME_PATH%"
    
    REM 컨테이너 상태 확인
    timeout /t 3 /nobreak >nul
    docker ps | findstr "%CONTAINER_NAME%"
)
goto :eof

REM 컨테이너 테스트
:test_container
call :log_info "컨테이너 테스트 시작..."

REM 컨테이너가 실행 중인지 확인
docker ps | findstr "%CONTAINER_NAME%" >nul 2>&1
if errorlevel 1 (
    call :log_error "컨테이너가 실행되지 않았습니다. 먼저 실행해주세요."
    exit /b 1
)

REM 헬스체크
call :log_info "헬스체크 수행..."
for /l %%i in (1,1,10) do (
    curl -s "http://localhost:%PORT%/health" >nul 2>&1
    if not errorlevel 1 (
        call :log_success "헬스체크 성공 (시도: %%i)"
        goto :health_check_success
    ) else if %%i==10 (
        call :log_error "헬스체크 실패 (10회 시도 후)"
        exit /b 1
    ) else (
        call :log_info "헬스체크 대기 중... (시도: %%i/10)"
        timeout /t 2 /nobreak >nul
    )
)

:health_check_success
REM API 엔드포인트 테스트
call :log_info "API 엔드포인트 테스트..."

REM 상태 확인
curl -s "http://localhost:%PORT%/status" >nul 2>&1
if not errorlevel 1 (
    call :log_success "상태 확인 API 테스트 성공"
) else (
    call :log_warning "상태 확인 API 테스트 실패"
)

REM 컨테이너 로그 확인
call :log_info "최근 컨테이너 로그:"
docker logs --tail 20 "%CONTAINER_NAME%"

call :log_success "컨테이너 테스트 완료"
goto :eof

REM 컨테이너 중지
:stop_container
call :log_info "컨테이너 중지..."

docker ps | findstr "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    docker stop "%CONTAINER_NAME%"
    call :log_success "컨테이너 중지 완료: %CONTAINER_NAME%"
) else (
    call :log_info "실행 중인 컨테이너가 없습니다: %CONTAINER_NAME%"
)
goto :eof

REM 컨테이너 로그 확인
:show_logs
call :log_info "컨테이너 로그 확인..."

docker ps -a | findstr "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    docker logs -f "%CONTAINER_NAME%"
) else (
    call :log_error "컨테이너를 찾을 수 없습니다: %CONTAINER_NAME%"
    exit /b 1
)
goto :eof

REM 컨테이너 내부 접속
:access_shell
call :log_info "컨테이너 내부 접속..."

docker ps | findstr "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    docker exec -it "%CONTAINER_NAME%" /bin/bash
) else (
    call :log_error "컨테이너가 실행되지 않았습니다. 먼저 실행해주세요."
    exit /b 1
)
goto :eof

REM 정리 작업
:clean_all
call :log_info "Docker 리소스 정리 시작..."

REM 컨테이너 중지 및 제거
docker ps -a | findstr "%CONTAINER_NAME%" >nul 2>&1
if not errorlevel 1 (
    call :log_info "컨테이너 제거: %CONTAINER_NAME%"
    docker stop "%CONTAINER_NAME%" 2>nul
    docker rm "%CONTAINER_NAME%" 2>nul
)

REM 이미지 제거
docker images | findstr "%IMAGE_NAME%" >nul 2>&1
if not errorlevel 1 (
    call :log_info "이미지 제거: %IMAGE_NAME%:%IMAGE_TAG%"
    docker rmi "%IMAGE_NAME%:%IMAGE_TAG%" 2>nul
)

REM 네트워크 제거
docker network ls | findstr "%NETWORK_NAME%" >nul 2>&1
if not errorlevel 1 (
    call :log_info "네트워크 제거: %NETWORK_NAME%"
    docker network rm "%NETWORK_NAME%" 2>nul
)

REM 출력 디렉토리 정리 (선택사항)
set /p "CLEAN_OUTPUT=출력 디렉토리도 정리하시겠습니까? (y/N): "
if /i "%CLEAN_OUTPUT%"=="y" (
    call :log_info "출력 디렉토리 정리"
    if exist "output" rmdir /s /q "output"
)

call :log_success "Docker 리소스 정리 완료"
goto :eof

REM 전체 과정 실행
:run_all
call :log_info "전체 과정 실행 시작..."

call :check_docker
call :create_network
call :build_image
call :run_container
call :test_container

call :log_success "전체 과정 완료!"
call :log_info "애플리케이션 접속: http://localhost:%PORT%"
goto :eof

REM 메인 로직
:main
if "%1"=="" goto :show_help
if "%1"=="build" goto :build_image
if "%1"=="run" goto :run_container
if "%1"=="test" goto :test_container
if "%1"=="stop" goto :stop_container
if "%1"=="clean" goto :clean_all
if "%1"=="logs" goto :show_logs
if "%1"=="shell" goto :access_shell
if "%1"=="all" goto :run_all
if "%1"=="help" goto :show_help
goto :show_help

REM 스크립트 실행
call :main %*