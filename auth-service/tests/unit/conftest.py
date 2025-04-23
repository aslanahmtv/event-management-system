import os
import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from dependency_injector import containers, providers

from app.main import create_app
from app.apis.containers import AppContainer
from app.apis.repositories import get_repository
from app.apis.user.models import UserDB  # Import the model directly

# Set testing environment
os.environ["TESTING"] = "1"

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for tests"""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
def test_container():
    """Create a test container with memory repositories"""
    container = AppContainer()
    
    # Override repositories with MemoryRepo
    repo_provider = providers.Factory(get_repository, "MemoryRepo")
    container.repository.override(repo_provider)
    
    # Override user_repository directly with the UserDB model (not through user_model)
    container.auth_container.user_repository.override(
        providers.Factory(get_repository, "MemoryRepo", model=UserDB)
    )
    
    # Wire the container
    container.wire(
        modules=[
            "app.apis.user.routers", 
            "app.apis.user.service"
        ]
    )
    
    return container

@pytest.fixture(scope="session")
def app(test_container):
    """Create test application"""
    app = create_app(test_container)
    return app

@pytest.fixture(scope="session")
def test_client(app):
    """Create test client"""
    with TestClient(app) as client:
        yield client

@pytest_asyncio.fixture
async def client(app):
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client