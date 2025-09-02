# DocQuestionReport Agent Makefile
# 사용법: make [target]

.PHONY: help build run test clean logs shell docker-build docker-run docker-test docker-clean docker-compose-up docker-compose-down

# 변수 정의
IMAGE_NAME = doc-question-report-agent
IMAGE_TAG = latest
CONTAINER_NAME = doc-question-report-agent-container
PORT = 8000

# 기본 타겟
help: ## 도움말 출력
	@echo "DocQuestionReport Agent Makefile"
	@echo ""
	@echo "사용법: make [target]"
	@echo ""
	@echo "타겟:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'

# Python 관련 타겟
install: ## Python 의존성 설치
	pip install -e .

install-dev: ## 개발 의존성 설치
	pip install -e ".[dev]"

test: ## 테스트 실행
	pytest tests/ -v --cov=doc_question_report_agent --cov-report=html --cov-report=term

test-coverage: ## 테스트 커버리지 보고서 생성
	pytest tests/ --cov=doc_question_report_agent --cov-report=html --cov-report=term --cov-report=xml

lint: ## 코드 린팅
	black .
	isort .
	flake8 .
	mypy .

format: ## 코드 포맷팅
	black .
	isort .

# Docker 관련 타겟
docker-build: ## Docker 이미지 빌드
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) .

docker-run: ## Docker 컨테이너 실행
	docker run -d --name $(CONTAINER_NAME) -p $(PORT):8000 -v $(PWD)/output:/app/output $(IMAGE_NAME):$(IMAGE_TAG)

docker-stop: ## Docker 컨테이너 중지
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true

docker-logs: ## Docker 컨테이너 로그 확인
	docker logs -f $(CONTAINER_NAME)

docker-shell: ## Docker 컨테이너 내부 접속
	docker exec -it $(CONTAINER_NAME) /bin/bash

docker-clean: ## Docker 리소스 정리
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME):$(IMAGE_TAG) || true

# Docker Compose 관련 타겟
docker-compose-up: ## Docker Compose로 서비스 시작
	docker-compose up -d

docker-compose-down: ## Docker Compose 서비스 중지
	docker-compose down

docker-compose-logs: ## Docker Compose 로그 확인
	docker-compose logs -f

docker-compose-restart: ## Docker Compose 서비스 재시작
	docker-compose restart

# 개발 관련 타겟
dev-install: install install-dev ## 개발 환경 설치

dev-run: ## 개발 모드로 실행
	python -m doc_question_report_agent.main

dev-test: test lint ## 개발 테스트 (테스트 + 린팅)

# 배포 관련 타겟
deploy: docker-build docker-run ## 배포 (빌드 + 실행)

deploy-full: docker-compose-up ## 전체 배포 (모니터링 포함)

# 정리 타겟
clean: ## Python 캐시 정리
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .pytest_cache/ .coverage htmlcov/ .mypy_cache/

clean-all: clean docker-clean ## 모든 리소스 정리

# 모니터링 타겟
monitoring-up: ## 모니터링 서비스 시작
	docker-compose up -d prometheus grafana

monitoring-down: ## 모니터링 서비스 중지
	docker-compose stop prometheus grafana

monitoring-logs: ## 모니터링 로그 확인
	docker-compose logs -f prometheus grafana

# 상태 확인 타겟
status: ## 서비스 상태 확인
	@echo "=== Docker 컨테이너 상태 ==="
	docker ps -a | grep $(CONTAINER_NAME) || echo "컨테이너가 실행되지 않음"
	@echo ""
	@echo "=== Docker 이미지 상태 ==="
	docker images | grep $(IMAGE_NAME) || echo "이미지가 없음"
	@echo ""
	@echo "=== 포트 사용 상태 ==="
	lsof -i :$(PORT) || echo "포트 $(PORT) 사용 중이 아님"

health: ## 헬스체크
	@echo "헬스체크 수행 중..."
	@curl -s http://localhost:$(PORT)/health > /dev/null && echo "✅ 서비스 정상" || echo "❌ 서비스 오류"

# 전체 워크플로우 타겟
workflow: ## 전체 워크플로우 실행 (빌드 → 테스트 → 배포)
	@echo "=== 전체 워크플로우 시작 ==="
	@make docker-build
	@make test
	@make docker-run
	@echo "=== 워크플로우 완료 ==="
	@echo "서비스 접속: http://localhost:$(PORT)"

# 문서 생성 타겟
docs: ## 문서 생성
	@echo "문서 생성 중..."
	@mkdir -p docs
	@echo "# DocQuestionReport Agent 문서" > docs/README.md
	@echo "" >> docs/README.md
	@echo "생성 시간: $(shell date)" >> docs/README.md
	@echo "문서가 docs/ 디렉토리에 생성되었습니다."

# 환경 설정 타겟
env-setup: ## 환경 설정 파일 생성
	@if [ ! -f .env ]; then \
		echo "환경 설정 파일 생성 중..."; \
		cp env.example .env; \
		echo ".env 파일이 생성되었습니다. 필요한 설정을 수정해주세요."; \
	else \
		echo ".env 파일이 이미 존재합니다."; \
	fi

# 초기 설정 타겟
init: env-setup dev-install ## 초기 설정 (환경 설정 + 의존성 설치)

# 도움말 (기본 타겟)
.DEFAULT_GOAL := help