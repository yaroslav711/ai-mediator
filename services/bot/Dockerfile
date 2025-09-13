FROM python:3.11-slim

# Аргумент для выбора пакетного менеджера
ARG USE_UV=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv if requested
RUN if [ "$USE_UV" = "true" ]; then \
    curl -LsSf https://astral.sh/uv/install.sh | sh; \
    fi

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY shared/ ./shared/
COPY services/bot/ ./services/bot/

# Install dependencies
RUN if [ "$USE_UV" = "true" ]; then \
    uv sync --extra bot --no-dev; \
    else \
    pip install -e ".[bot]"; \
    fi

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "services.bot.app.main"]
