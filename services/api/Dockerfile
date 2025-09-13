FROM python:3.11-slim

# Аргумент для выбора пакетного менеджера
ARG USE_UV=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
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
COPY services/api/ ./services/api/

# Install dependencies
RUN if [ "$USE_UV" = "true" ]; then \
    uv sync --extra api --no-dev; \
    else \
    pip install -e ".[api]"; \
    fi

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "-m", "uvicorn", "services.api.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
