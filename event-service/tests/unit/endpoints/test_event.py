"""Unit testing for app.apis.event.routers"""
# pylint: disable=redefined-outer-name

import json
import uuid
from datetime import datetime, timedelta
import pytest
import pytest_asyncio
from fastapi import status

from app.apis.event.models import EventDB, EventStatus, GeoPoint
from app.apis.event.schemas import EventSubscription
from pydantic_factories import ModelFactory


class EventDBFactory(ModelFactory):
    __model__ = EventDB
    
    @classmethod
    def get_mock_event_data(cls):
        """Generate valid event data for testing"""
        future_date = datetime.now() + timedelta(days=10)
        return {
            "title": f"Test Event {uuid.uuid4().hex[:8]}",
            "description": "This is a test event",
            "location": "Test Location",
            "start_time": future_date.isoformat(),
            "end_time": (future_date + timedelta(hours=2)).isoformat(),
            "tags": ["test", "event"],
            "max_attendees": 100,
            "status": EventStatus.SCHEDULED,
            "attachment_url": "https://example.com/attachment.pdf",
            "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
            "created_by": "test_user_1"
        }


# Create 10 mock events with realistic data
mocked_events = []
for _ in range(10):
    event_data = EventDBFactory.get_mock_event_data()
    event_data["event_id"] = uuid.uuid4().hex
    event_data["created_at"] = datetime.now().isoformat()
    event_data["updated_at"] = datetime.now().isoformat()
    event_data["subscribers"] = []
    mocked_events.append(EventDB(**event_data))


@pytest_asyncio.fixture(scope="module", autouse=True)
async def mocked_repo(app):
    """Set up mocked repository with test events"""
    repo = app.container.event_container.event_repository()
    _ = [repo.add(mocked_event) for mocked_event in mocked_events]
    return repo


@pytest_asyncio.fixture
async def auth_headers():
    """Mock JWT auth headers for protected endpoints"""
    return {"Authorization": "Bearer mock_token"}


# 1. Test GET /events/{event_id} endpoint
@pytest.mark.asyncio
async def test_get_event_exists(client, auth_headers):
    """Test retrieving an existing event by ID"""
    for event in mocked_events:
        event_id = event.event_id
        response = await client.get(
            f"/events/{event_id}",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        result = response.json()
        assert result["event_id"] == event_id
        assert result["title"] == event.title
        assert result["description"] == event.description


@pytest.mark.asyncio
async def test_get_event_not_exists(client, auth_headers):
    """Test retrieving a non-existent event by ID"""
    not_valid_event_id = "non_existent_id"
    response = await client.get(
        f"/events/{not_valid_event_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 2. Test GET /events endpoint (with pagination)
@pytest.mark.asyncio
async def test_get_all_events(client, auth_headers):
    """Test retrieving all events with default pagination"""
    response = await client.get(
        "/events",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "events" in result
    assert "total" in result
    assert "page" in result
    assert "page_size" in result
    assert result["page"] == 1
    

@pytest.mark.asyncio
async def test_get_events_with_pagination(client, auth_headers):
    """Test retrieving events with custom pagination"""
    response = await client.get(
        "/events?page=2&page_size=3",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["page"] == 2
    assert result["page_size"] == 3
    assert len(result["events"]) <= 3


@pytest.mark.asyncio
async def test_get_events_with_tag_filter(client, auth_headers):
    """Test retrieving events filtered by tag"""
    response = await client.get(
        "/events?tag=test",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    # Check that all returned events have the "test" tag
    if result["events"]:
        for event in result["events"]:
            assert "test" in event["tags"]


@pytest.mark.asyncio
async def test_get_events_with_status_filter(client, auth_headers):
    """Test retrieving events filtered by status"""
    response = await client.get(
        "/events?status=scheduled",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    # Check that all returned events have "scheduled" status
    if result["events"]:
        for event in result["events"]:
            assert event["status"] == "scheduled"


# 3. Test POST /events endpoint
@pytest.mark.asyncio
async def test_create_event(client, mocked_repo, auth_headers):
    """Test creating a new event"""
    event_data = EventDBFactory.get_mock_event_data()
    
    response = await client.post(
        "/events",
        json=event_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()
    assert "event_id" in result
    assert result["title"] == event_data["title"]
    
    # Verify event was created in the repository
    created_event = mocked_repo.filter_by(event_id=result["event_id"]).first()
    assert created_event is not None
    assert created_event.title == event_data["title"]


@pytest.mark.asyncio
async def test_create_event_invalid_dates(client, auth_headers):
    """Test creating an event with invalid dates (end before start)"""
    event_data = EventDBFactory.get_mock_event_data()
    # Set end_time before start_time
    future_date = datetime.now() + timedelta(days=10)
    event_data["start_time"] = (future_date + timedelta(hours=2)).isoformat()
    event_data["end_time"] = future_date.isoformat()
    
    response = await client.post(
        "/events",
        json=event_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_create_event_past_date(client, auth_headers):
    """Test creating an event with a past date"""
    event_data = EventDBFactory.get_mock_event_data()
    # Set start_time in the past
    past_date = datetime.now() - timedelta(days=1)
    event_data["start_time"] = past_date.isoformat()
    event_data["end_time"] = (past_date + timedelta(hours=2)).isoformat()
    
    response = await client.post(
        "/events",
        json=event_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# 4. Test PATCH /events/{event_id} endpoint
@pytest.mark.asyncio
async def test_update_event(client, mocked_repo, auth_headers):
    """Test updating an existing event"""
    event = mocked_events[0]
    event_id = event.event_id
    
    update_data = {
        "title": "Updated Event Title",
        "description": "Updated description"
    }
    
    response = await client.patch(
        f"/events/{event_id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["event_id"] == event_id
    assert result["title"] == update_data["title"]
    assert result["description"] == update_data["description"]
    
    # Verify event was updated in the repository
    updated_event = mocked_repo.filter_by(event_id=event_id).first()
    assert updated_event.title == update_data["title"]
    assert updated_event.description == update_data["description"]


@pytest.mark.asyncio
async def test_update_nonexistent_event(client, auth_headers):
    """Test attempting to update a non-existent event"""
    non_existent_id = "non_existent_id"
    
    update_data = {
        "title": "Updated Event Title",
    }
    
    response = await client.patch(
        f"/events/{non_existent_id}",
        json=update_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 5. Test DELETE /events/{event_id} endpoint
@pytest.mark.asyncio
async def test_delete_event(client, mocked_repo, auth_headers):
    """Test deleting an existing event"""
    # Use the last mocked event to avoid conflicts with other tests
    event = mocked_events[-1]
    event_id = event.event_id
    
    # Verify the event exists before deletion
    existing_event = mocked_repo.filter_by(event_id=event_id).first()
    assert existing_event is not None
    
    response = await client.delete(
        f"/events/{event_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # Verify the event was deleted
    deleted_event = mocked_repo.filter_by(event_id=event_id).first()
    assert deleted_event is None


@pytest.mark.asyncio
async def test_delete_nonexistent_event(client, auth_headers):
    """Test attempting to delete a non-existent event"""
    non_existent_id = "non_existent_id"
    
    response = await client.delete(
        f"/events/{non_existent_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 6. Test POST /events/subscribe endpoint
@pytest.mark.asyncio
async def test_subscribe_to_event(client, mocked_repo, auth_headers):
    """Test subscribing to event updates"""
    event = mocked_events[1]  # Use second event to avoid conflicts
    event_id = event.event_id
    
    subscription_data = {
        "event_id": event_id
    }
    
    response = await client.post(
        "/events/subscribe",
        json=subscription_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["status"] == "success"
    assert event_id in result["message"]
    
    # Verify user was added to subscribers in the repository
    # This depends on how your subscribe_user_to_event method is implemented
    # Assuming it adds the user_id to the subscribers list
    updated_event = mocked_repo.filter_by(event_id=event_id).first()
    assert "test_user_1" in updated_event.subscribers


@pytest.mark.asyncio
async def test_subscribe_to_nonexistent_event(client, auth_headers):
    """Test subscribing to a non-existent event"""
    non_existent_id = "non_existent_id"
    
    subscription_data = {
        "event_id": non_existent_id
    }
    
    response = await client.post(
        "/events/subscribe",
        json=subscription_data,
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# 7. Test DELETE /events/unsubscribe/{event_id} endpoint
@pytest.mark.asyncio
async def test_unsubscribe_from_event(client, mocked_repo, auth_headers):
    """Test unsubscribing from event updates"""
    # First subscribe to an event
    event = mocked_events[2]  # Use third event to avoid conflicts
    event_id = event.event_id
    
    # Ensure the user is subscribed first (add to subscribers list)
    existing_event = mocked_repo.filter_by(event_id=event_id).first()
    if "test_user_1" not in existing_event.subscribers:
        existing_event.subscribers.append("test_user_1")
        mocked_repo.filter_by(event_id=event_id).update(subscribers=existing_event.subscribers)
    
    response = await client.delete(
        f"/events/unsubscribe/{event_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["status"] == "success"
    assert event_id in result["message"]
    
    # Verify user was removed from subscribers in the repository
    updated_event = mocked_repo.filter_by(event_id=event_id).first()
    assert "test_user_1" not in updated_event.subscribers


@pytest.mark.asyncio
async def test_unsubscribe_from_nonexistent_event(client, auth_headers):
    """Test unsubscribing from a non-existent event"""
    non_existent_id = "non_existent_id"
    
    response = await client.delete(
        f"/events/unsubscribe/{non_existent_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


# Authentication tests
@pytest.mark.asyncio
async def test_endpoints_require_authentication(client):
    """Test that endpoints require authentication"""
    # Try accessing an endpoint without auth headers
    response = await client.get("/events")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "not authenticated" in response.json()["detail"].lower()