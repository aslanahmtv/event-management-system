"""Unit testing for app.apis.notification.routers"""
# pylint: disable=redefined-outer-name

import json
import uuid
import asyncio
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from fastapi import status
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

from app.apis.notification.models import NotificationDB, NotificationType
from pydantic_factories import ModelFactory


class NotificationDBFactory(ModelFactory):
    __model__ = NotificationDB
    
    @classmethod
    def get_mock_notification_data(cls, user_id="test_user_1"):
        """Generate valid notification data for testing"""
        event_id = uuid.uuid4().hex
        return {
            "type": "notification",
            "notification_type": NotificationType.EVENT_CREATED,
            "event": {
                "id": event_id,
                "title": f"Test Event {uuid.uuid4().hex[:8]}",
                "action": "created",
                "timestamp": datetime.now().isoformat()
            },
            "user": user_id,
            "delivered_to": [user_id]
        }


# Create 10 mock notifications with realistic data
mocked_notifications = []
for _ in range(10):
    notification_data = NotificationDBFactory.get_mock_notification_data()
    notification_data["notification_id"] = uuid.uuid4().hex
    notification_data["timestamp"] = datetime.now().isoformat()
    mocked_notifications.append(NotificationDB(**notification_data))


@pytest_asyncio.fixture(scope="module", autouse=True)
async def mocked_repo(app):
    """Set up mocked repository with test notifications"""
    repo = app.container.notification_container.notification_repository()
    _ = [repo.add(notification) for notification in mocked_notifications]
    return repo


@pytest_asyncio.fixture
async def auth_headers():
    """Mock JWT auth headers for protected endpoints"""
    return {"Authorization": "Bearer mock_token"}


# 1. Test GET /notifications endpoint (with pagination)
@pytest.mark.asyncio
async def test_get_all_notifications(client, auth_headers):
    """Test retrieving all notifications with default pagination"""
    response = await client.get(
        "/notifications",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert isinstance(result, list)
    assert len(result) <= 10  # Default page size


@pytest.mark.asyncio
async def test_get_notifications_with_pagination(client, auth_headers):
    """Test retrieving notifications with custom pagination"""
    response = await client.get(
        "/notifications?page=2&page_size=3",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert isinstance(result, list)
    assert len(result) <= 3


# 2. Test GET /notifications/count endpoint
@pytest.mark.asyncio
async def test_get_notification_count(client, auth_headers):
    """Test retrieving notification count"""
    response = await client.get(
        "/notifications/count",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "count" in result
    assert isinstance(result["count"], int)


# 3. Test GET /notifications/{notification_id} endpoint
@pytest.mark.asyncio
async def test_get_notification_exists(client, auth_headers):
    """Test retrieving an existing notification by ID"""
    for notification in mocked_notifications:
        notification_id = notification.notification_id
        response = await client.get(
            f"/notifications/{notification_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["notification_id"] == notification_id
        assert result["type"] == notification.type
        assert result["notification_type"] == notification.notification_type


@pytest.mark.asyncio
async def test_get_notification_not_exists(client, auth_headers):
    """Test retrieving a non-existent notification by ID"""
    not_valid_notification_id = "non_existent_id"
    response = await client.get(
        f"/notifications/{not_valid_notification_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 4. Test POST /notifications/mark-read/{notification_id} endpoint
@pytest.mark.asyncio
async def test_mark_notification_read(client, mocked_repo, auth_headers):
    """Test marking a notification as read"""
    notification = mocked_notifications[0]
    notification_id = notification.notification_id
    
    response = await client.post(
        f"/notifications/mark-read/{notification_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["status"] == "success"
    assert notification_id in result["message"]


@pytest.mark.asyncio
async def test_mark_nonexistent_notification_read(client, auth_headers):
    """Test marking a non-existent notification as read"""
    non_existent_id = "non_existent_id"
    
    response = await client.post(
        f"/notifications/mark-read/{non_existent_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 5. Test POST /notifications/mark-all-read endpoint
@pytest.mark.asyncio
async def test_mark_all_notifications_read(client, mocked_repo, auth_headers):
    """Test marking all notifications as read"""
    response = await client.post(
        "/notifications/mark-all-read",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["status"] == "success"
    assert "marked" in result["message"].lower()


@pytest.mark.asyncio
async def test_websocket_unauthorized_connection(test_client):
    """Test WebSocket connection without authentication"""
    with pytest.raises(WebSocketDisconnect):
        with test_client.websocket_connect("/ws") as websocket:
            pass

# 6. Test Authentication requirements
@pytest.mark.asyncio
async def test_endpoints_require_authentication(client):
    """Test that endpoints require authentication"""
    # Try accessing an endpoint without auth headers
    response = await client.get("/notifications")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "not authenticated" in response.json()["detail"].lower()
