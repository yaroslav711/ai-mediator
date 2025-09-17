.PHONY: help install dev-install test lint format clean docker-build docker-up docker-down prompt-test

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install all dependencies (using uv)
	uv sync

dev-install: ## Install development dependencies (using uv)
	uv sync --extra dev --extra tools

install-api: ## Install only API dependencies
	uv sync --extra api --extra dev

install-bot: ## Install only Bot dependencies  
	uv sync --extra bot --extra dev

# Legacy pip approach (если uv не работает)
install-pip: ## Install with pip (fallback)
	pip install -e ".[dev,api,bot,tools]"

# Testing
test: ## Run all tests
	python -m pytest tests/

test-unit: ## Run unit tests only
	python -m pytest tests/

test-integration: ## Run integration tests only
	python -m pytest tests/integration/

test-e2e: ## Run end-to-end tests
	python -m pytest tests/e2e/

test-prompts: ## Run prompt tests only
	python -m pytest shared/prompts/tests/

# Code quality
lint: ## Run linting
	export PATH="/Users/$(USER)/.local/bin:$$PATH" && uv run ruff check internal/ shared/ tools/ main/

format: ## Format code
	export PATH="/Users/$(USER)/.local/bin:$$PATH" && uv run ruff format internal/ shared/ tools/ main/

# Database
db-upgrade: ## Apply database migrations
	cd shared/database && alembic upgrade head

db-downgrade: ## Rollback database migration
	cd shared/database && alembic downgrade -1

db-migration: ## Create new migration (usage: make db-migration message="description")
	cd shared/database && alembic revision --autogenerate -m "$(message)"

# Docker
docker-build: ## Build all Docker images
	docker-compose build

docker-up: ## Start all services
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Show logs from all services
	docker-compose logs -f

# Development tools
prompt-test: ## Run prompt tests
	python tools/prompt_tester.py --all

prompt-playground: ## Start interactive prompt playground
	python tools/prompt_playground.py

prompt-test-single: ## Run single prompt test (usage: make prompt-test-single case=test_name)
	python tools/prompt_tester.py --test-case $(case)

seed-data: ## Seed database with test data
	python tools/data_seeder.py

# Cleaning
clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

# Environment setup
setup-dev: ## Setup development environment
	python tools/dev_setup.py
	make dev-install
	make db-upgrade
	make seed-data
