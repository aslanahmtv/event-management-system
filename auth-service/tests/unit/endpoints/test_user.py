"""Unit testing for app.apis.user.routers"""
# pylint: disable=redefined-outer-name

import json
from datetime import datetime
import uuid
import pytest
import pytest_asyncio
from fastapi import status

from app.apis.user.models import UserDB
from app.apis.user.schemas import UserRegister
from app.apis.user.security import hash_password
from pydantic_factories import ModelFactory


class UserDBFactory(ModelFactory):
    __model__ = UserDB
    
    @classmethod
    def get_mock_user_data(cls):
        """Generate valid user data for testing"""
        user_id = uuid.uuid4().hex
        return {
            "user_id": user_id,
            "email": f"test{user_id[:8]}@example.com",
            "username": f"testuser_{user_id[:8]}",
            "password_hash": hash_password("Test1234!"),
            "full_name": f"Test User {user_id[:8]}",
            "is_active": True,
            "is_verified": False,
            "role": "user",
            "created_at": datetime.now().isoformat(),  # Make datetime JSON serializable
            "updated_at": datetime.now().isoformat(),  # Make datetime JSON serializable
            "last_login": None
        }


# Create mock users
mocked_users = []
for _ in range(10):
    user_data = UserDBFactory.get_mock_user_data()
    mocked_users.append(UserDB(**user_data))


@pytest_asyncio.fixture(scope="module", autouse=True)
async def mocked_repo(app):
    """Set up mocked repository with test users"""
    repo = app.container.auth_container.user_repository()
    _ = [repo.add(user) for user in mocked_users]
    return repo


@pytest_asyncio.fixture
async def auth_token(client):
    """Get authentication token for testing"""
    # Register a test user first
    user_id = uuid.uuid4().hex
    user_data = {
        "email": f"testauth{user_id[:8]}@example.com",
        "username": f"testauth{user_id[:8]}",
        "password": "Test1234!",
        "full_name": "Test Auth User"
    }
    
    # Register a new user for each test
    reg_response = await client.post("/auth/register", json=user_data)
    
    # Login with the user
    login_response = await client.post(
        "/auth/login",
        json={"username_or_email": user_data["username"], "password": "Test1234!"}
    )
    
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    return token_data["access_token"]


@pytest_asyncio.fixture
async def auth_headers(auth_token):
    """Get authentication headers"""
    return {"Authorization": f"Bearer {auth_token}"}


# 1. Test /auth/register endpoint
@pytest.mark.asyncio
async def test_register_user(client):
    """Test user registration"""
    # Generate unique user data for registration
    user_id = uuid.uuid4().hex
    user_data = {
        "email": f"newuser{user_id[:8]}@example.com",
        "username": f"newuser_{user_id[:8]}",
        "password": "Test1234!",
        "full_name": f"New User {user_id[:8]}"
    }
    
    response = await client.post("/auth/register", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED
    
    result = response.json()
    assert result["email"] == user_data["email"]
    assert result["username"] == user_data["username"]
    assert "password" not in result  # Password should not be returned
    assert result["full_name"] == user_data["full_name"]


# 2. Test /auth/login endpoint
@pytest.mark.asyncio
async def test_login_user(client):
    """Test user login"""
    # First register a user
    user_id = uuid.uuid4().hex
    user_data = {
        "email": f"logintest{user_id[:8]}@example.com",
        "username": f"logintest_{user_id[:8]}",
        "password": "Test1234!",
        "full_name": f"Login Test User {user_id[:8]}"
    }
    
    await client.post("/auth/register", json=user_data)
    
    # Now try to login
    login_data = {
        "username_or_email": user_data["username"],
        "password": user_data["password"]
    }
    
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == status.HTTP_200_OK
    
    token_data = response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    assert "expires_in" in token_data


# 3. Test /auth/me endpoint
@pytest.mark.asyncio
async def test_get_current_user(client, auth_headers):
    """Test getting current user info"""
    response = await client.get("/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    
    user_data = response.json()
    assert "user_id" in user_data
    assert "email" in user_data
    assert "username" in user_data


# 4. Test /users/{user_id} endpoint
@pytest.mark.asyncio
async def test_get_user_exists(client, auth_headers):
    """Test getting existing user"""
    for user in mocked_users:
        user_id = user.user_id
        response = await client.get(
            f"/users/{user_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        
        result = response.json()
        assert result["user_id"] == user_id
        assert result["email"] == user.email
        assert result["username"] == user.username


@pytest.mark.asyncio
async def test_get_user_not_exists(client, auth_headers):
    """Test getting non-existent user"""
    not_valid_user_id = uuid.uuid4().hex
    response = await client.get(
        f"/users/{not_valid_user_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 5. Test rate limiting for login
@pytest.mark.asyncio
async def test_login_rate_limiting(client):
    """Test that login endpoint has rate limiting"""
    # This test may need to be adjusted based on your actual rate limit settings
    # For example, if it's 5 requests per minute, we'll make 6 requests
    login_data = {
        "username_or_email": "nonexistent_user",
        "password": "wrongpassword"
    }
    
    # Make multiple login attempts
    responses = []
    for _ in range(6):  # Adjust this number based on your rate limit
        response = await client.post("/auth/login", json=login_data)
        responses.append(response)
    
    # At least one of the responses should have a 429 status code
    assert any(r.status_code == status.HTTP_429_TOO_MANY_REQUESTS for r in responses), \
        "Rate limiting not working correctly"


# 6. Test authentication required for protected endpoints
@pytest.mark.asyncio
async def test_authentication_required(client):
    """Test that endpoints require authentication"""
    # Test /auth/me endpoint
    response = await client.get("/auth/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    # Test /users/{user_id} endpoint
    user_id = mocked_users[0].user_id
    response = await client.get(f"/users/{user_id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


# 7. Sanity check
@pytest.mark.asyncio
async def test_sanity_check(client):
    """Test basic API connectivity"""
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == "FastAPI running!"