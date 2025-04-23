from asyncio import get_event_loop

import pytest_asyncio
import pytest
from dependency_injector import providers
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.apis.containers import AppContainer
from app.apis.repositories import get_repository
from app.apis.notification.models import NotificationDB
from app.main import create_app


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def app():
    container = AppContainer(
        repository=providers.Singleton(get_repository, "MemoryRepo"),
    )
    return create_app(container)


@pytest.fixture
def test_client(app):
    """Create a test client for WebSocket testing"""
    with TestClient(app) as client:
        yield client


@pytest_asyncio.fixture(scope="module")
async def client(app):
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c