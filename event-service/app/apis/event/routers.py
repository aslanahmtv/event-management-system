"""Module with the routers related to the event service"""
from typing import Any, Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer

from app.apis.auth.jwt import get_current_user_id  # JWT validation utility

from .schemas import EventCreate, EventList, EventResponse, EventSubscription, EventUpdate
from .service import EventService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


@inject
def get_event_router(event_service: EventService = Provide["event_container.event_service"]):
    router = APIRouter()

    @router.post(
        "",
        response_model=EventResponse,
        response_description="Add new event",
        status_code=status.HTTP_201_CREATED,
        tags=["events"],
    )
    async def create_event(
        event: EventCreate = Body(...), token: str = Depends(oauth2_scheme)
    ) -> EventResponse:
        """
        Create a new event with the given event details.

        - **title**: Event title (1-100 characters)
        - **description**: Event description
        - **location**: Event location
        - **start_time**: Event start time
        - **end_time**: Event end time (must be after start_time)
        - **tags**: Optional list of event tags
        - **max_attendees**: Optional maximum number of attendees
        - **status**: Event status (scheduled, canceled, completed)
        - **attachment_url**: Optional URL for event attachments
        - **coordinates**: Optional GeoJSON point (latitude, longitude)
        """
        user_id = get_current_user_id(token)
        return await event_service.create_event(event, user_id)

    @router.get(
        "",
        response_model=EventList,  # Change this from List[EventResponse] to EventList
        response_description="Get all events",
        status_code=status.HTTP_200_OK,
        tags=["events"],
    )
    async def get_events(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Number of events per page"),
        tag: Optional[str] = Query(None, description="Filter events by tag"),
        status_filter: Optional[str] = Query(None, alias="status", description="Filter events by status"),
        token: str = Depends(oauth2_scheme),
    ) -> Dict[str, Any]:  # Change return type to Dict
        """
        Retrieve all events with optional pagination and filtering.
        
        - **page**: Page number (starting from 1)
        - **page_size**: Number of events per page (max 100)
        - **tag**: Optional tag to filter events by
        - **status**: Optional status to filter events by
        """
        user_id = get_current_user_id(token)
        events = await event_service.get_all_events(
            page=page, 
            page_size=page_size,
            tag=tag,
            status=status_filter
        )
        
        # Calculate total count (for pagination)
        all_events = event_service.event_repo.filter_by().all()
        
        # Return dictionary with events and pagination info
        return {
            "events": [EventResponse.from_event_db(event) for event in events],
            "total": len(all_events),
            "page": page,
            "page_size": page_size
        }

    @router.get(
        "/{event_id}",
        response_model=EventResponse,
        response_description="Get a single event",
        status_code=status.HTTP_200_OK,
        tags=["events"],
    )
    async def get_event(event_id: str, token: str = Depends(oauth2_scheme)) -> EventResponse:
        """
        Retrieve details for a specific event by ID.

        - **event_id**: The unique identifier of the event
        """
        get_current_user_id(token)
        event = await event_service.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found",
            )
        return event

    @router.patch(
        "/{event_id}",
        response_model=EventResponse,
        response_description="Update event",
        status_code=status.HTTP_200_OK,
        tags=["events"],
    )
    async def update_event(
        event_id: str, event: EventUpdate = Body(...), token: str = Depends(oauth2_scheme)
    ) -> EventResponse:
        """
        Update an existing event with the given details.

        - **event_id**: The unique identifier of the event to update
        - All event fields are optional for updates
        """
        user_id = get_current_user_id(token)
        updated_event = await event_service.update_event(event_id, event, user_id)
        return updated_event

    @router.delete(
        "/{event_id}",
        status_code=status.HTTP_204_NO_CONTENT,
        response_description="Delete event",
        tags=["events"],
    )
    async def delete_event(event_id: str, token: str = Depends(oauth2_scheme)) -> None:
        """
        Delete an event by ID.

        - **event_id**: The unique identifier of the event to delete
        """
        user_id = get_current_user_id(token)
        await event_service.delete_event(event_id, user_id)

    @router.post(
        "/subscribe",
        response_description="Subscribe to event updates",
        status_code=status.HTTP_200_OK,
        tags=["events", "notifications"],
    )
    async def subscribe_to_event(
        subscription: EventSubscription = Body(...), token: str = Depends(oauth2_scheme)
    ) -> Dict[str, str]:
        """
        Subscribe to updates for a specific event.

        - **event_id**: The unique identifier of the event to subscribe to
        """
        user_id = get_current_user_id(token)

        # Check if event exists
        event = await event_service.get_event(subscription.event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {subscription.event_id} not found",
            )

        # Subscribe user to event updates
        await event_service.subscribe_user_to_event(subscription.event_id, user_id)

        return {"status": "success", "message": f"Subscribed to event {subscription.event_id}"}

    @router.delete(
        "/unsubscribe/{event_id}",
        response_description="Unsubscribe from event updates",
        status_code=status.HTTP_200_OK,
        tags=["events", "notifications"],
    )
    async def unsubscribe_from_event(
        event_id: str, token: str = Depends(oauth2_scheme)
    ) -> Dict[str, str]:
        """
        Unsubscribe from updates for a specific event.

        - **event_id**: The unique identifier of the event to unsubscribe from
        """
        user_id = get_current_user_id(token)
        await event_service.unsubscribe_user_from_event(event_id, user_id)
        return {"status": "success", "message": f"Unsubscribed from event {event_id}"}

    return router
