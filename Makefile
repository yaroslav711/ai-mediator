.PHONY: help install dev-install test lint format clean docker-build docker-up docker-down prompt-test

# Default target
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development setup
install: ## Install/update dependencies (creates venv if needed)
	python3 -m venv venv --upgrade-deps
	./venv/bin/pip install -e .

install-deps: ## Install dependencies only (requires existing venv)
	@if [ ! -d "venv" ]; then echo "❌ Virtual environment not found. Run 'make install' first."; exit 1; fi
	./venv/bin/pip install -e .

dev-install: ## Install development dependencies  
	python3 -m venv venv --upgrade-deps
	./venv/bin/pip install -e ".[dev,tools]"

# Docker
docker-build: ## Build all Docker images
	docker-compose build

docker-up: ## Start all services
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Show logs from all services
	docker-compose logs -f

# Removed development tools - not needed yet

# Cleaning
clean: ## Clean temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +

clean-venv: ## Remove virtual environment
	rm -rf venv

reset: ## Complete reset (clean + remove venv)
	make clean
	make clean-venv
	@echo "🧹 Project reset complete. Run 'make setup' to start fresh."

# Environment setup
setup-dev: ## Setup development environment
	make dev-install
	make db-upgrade

# Quick start
start: ## Quick start application
	@if [ ! -d "venv" ]; then echo "❌ Virtual environment not found. Run 'make install' first."; exit 1; fi
	@if [ ! -f ".env" ]; then echo "❌ .env file not found. Copy .env.example to .env and fill in your tokens."; exit 1; fi
	@echo "🚀 Starting AI Mediator bot..."
	./venv/bin/python -m src.main

# Environment check
check-env: ## Check if environment is properly configured
	@echo "🔍 Checking environment configuration..."
	@if [ ! -d "venv" ]; then echo "❌ Virtual environment not found. Run 'make install' first."; exit 1; fi
	@./venv/bin/python -c "from src.config.settings import get_settings; s = get_settings(); print(f'✅ Bot: @{s.telegram_bot_username}'); print(f'✅ DB: {s.database_url}')" 2>/dev/null || echo "❌ Environment not configured. Copy .env.example to .env and fill in values."

# Complete setup
setup: ## Complete setup (install + configure)
	@echo "🔧 Setting up AI Mediator..."
	make install
	@if [ ! -f ".env" ]; then \
		cp .env.example .env; \
		echo "📝 Created .env file from example. Please edit it with your tokens:"; \
		echo "   - TELEGRAM_BOT_TOKEN (get from @BotFather)"; \
		echo "   - TELEGRAM_BOT_USERNAME (your bot username)"; \
		echo "   - OPENAI_API_KEY (get from OpenAI)"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@echo "🎉 Setup complete! Edit .env file and run 'make start'"
