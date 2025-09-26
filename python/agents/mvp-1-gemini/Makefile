install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/0.6.12/install.sh | sh; source $HOME/.local/bin/env; }
	uv sync && npm --prefix frontend install

dev:
	make dev-backend & make dev-frontend

dev-backend:
	uv run adk api_server app --allow_origins="*"

dev-frontend:
	npm --prefix frontend run dev

playground:
	uv run adk web --port 8501

lint:
	uv sync --dev --extra lint
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .

deploy-infra:
	echo "Skipping: Infra not required"

# Docker 관련 명령어
docker-build:
	./docker-run.sh build

docker-up:
	./docker-run.sh up

docker-down:
	./docker-run.sh down

docker-restart:
	./docker-run.sh restart

docker-logs:
	./docker-run.sh logs

docker-status:
	./docker-run.sh status

docker-health:
	./docker-run.sh health

docker-clean:
	./docker-run.sh clean

# Docker 개발 환경 전체 실행
docker-dev: docker-build docker-up
