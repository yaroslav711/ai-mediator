# Общие тестовые утилиты для тестов
import pytest
import asyncio
from typing import AsyncGenerator
import httpx


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Интеграционные тесты с testcontainers (опциональные)
try:
    from testcontainers.postgres import PostgresContainer
    from testcontainers.redis import RedisContainer
    TESTCONTAINERS_AVAILABLE = True
except ImportError:
    TESTCONTAINERS_AVAILABLE = False


@pytest.fixture(scope="session")
async def postgres_container():
    """Provide a PostgreSQL container for integration tests."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")

    with PostgresContainer("postgres:15") as postgres:
        yield postgres


@pytest.fixture(scope="session")
async def redis_container():
    """Provide a Redis container for integration tests."""
    if not TESTCONTAINERS_AVAILABLE:
        pytest.skip("testcontainers not available")

    with RedisContainer("redis:7-alpine") as redis:
        yield redis


@pytest.fixture
async def api_client(postgres_container, redis_container) -> AsyncGenerator[httpx.AsyncClient, None]:
    """HTTP client for API integration tests."""
    # TODO: Setup test API instance with test containers
    base_url = "http://localhost:8000"
    async with httpx.AsyncClient(base_url=base_url) as client:
        yield client
