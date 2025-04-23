"""Module with the Event service to serve"""
import json
from datetime import datetime
from typing import List, Optional

import aio_pika
from fastapi import HTTPException, status
from redbird.templates import TemplateRepo

from app.apis.config import settings

from .models import Event, EventDB
from .schemas import EventUpdate


class EventService:
    """Service to interact with event collection with message broker integration.

    Args:
        event_repo (TemplateRepo): Repository for the DB connection
    """

    def __init__(self, event_repo: TemplateRepo) -> None:
        self.event_repo = event_repo
        self.connection = None
        self.channel = None
        self.exchange = None
        self._init_broker()

    async def _init_broker(self) -> None:
        """Initialize connection to the message broker"""
        try:
            # Connect to RabbitMQ
            self.connection = await aio_pika.connect_robust(
                settings.BROKER_URL,
                max_attempts=settings.MAX_RETRIES,
                retry_delay=settings.RETRY_DELAY,
            )
            # Create channel
            self.channel = await self.connection.channel()
            # Declare exchange
            self.exchange = await self.channel.declare_exchange(
                settings.EXCHANGE_NAME, aio_pika.ExchangeType.TOPIC, durable=True
            )
        except Exception as e:
            # Log error but don't fail - service can still work without messaging
            print(f"Failed to connect to message broker: {str(e)}")

    async def _publish_event_message(
        self, event_id: str, event_title: str, action: str, user: str
    ) -> None:
        """Publish event change message to the broker"""
        if not self.exchange:
            # Attempt to reconnect if exchange is not available
            await self._init_broker()
            if not self.exchange:
                print("Message broker unavailable, skipping notification")
                return

        try:
            # Create the payload according to spec
            payload = {
                "type": "notification",
                "notification_type": f"event.{action}",
                "event": {
                    "id": event_id,
                    "title": event_title,
                    "action": action,
                    "timestamp": datetime.now().isoformat(),
                },
                "user": user,
            }

            # Create the message
            message = aio_pika.Message(
                body=json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )

            # Publish the message
            await self.exchange.publish(message, routing_key=f"event.{action}")
        except Exception as e:
            # Log the error but don't fail the operation
            print(f"Failed to publish message: {str(e)}")

    async def get_event(self, event_id: str) -> Optional[EventDB]:
        """Get an event by ID"""
        return self.event_repo.filter_by(event_id=event_id).first()

    async def get_all_events(
        self, 
        page: int = 1, 
        page_size: int = 10,
        tag: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[EventDB]:
        """Get all events with pagination and filtering
        
        Args:
            page: Page number (starting from 1)
            page_size: Number of events per page
            tag: Optional tag to filter events by
            status: Optional status to filter events by
            
        Returns:
            List of events
        """
        # Start with all events
        events = self.event_repo.filter_by().all()
        
        # Apply tag filter if provided
        if tag:
            events = [e for e in events if tag in (getattr(e, "tags", []) or [])]
        
        # Apply status filter if provided
        if status:
            events = [e for e in events if getattr(e, "status", None) == status]
        
        # Sort by start_time
        events.sort(key=lambda e: getattr(e, "start_time", datetime.max), reverse=False)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return events[start_idx:end_idx]

    async def create_event(self, event: Event, user_id: str) -> EventDB:
        """Create a new event and publish a notification

        Args:
            event: The event data
            user_id: The ID of the user creating the event

        Returns:
            EventDB: The created event
        """
        # Validate event dates
        if hasattr(event, "start_time") and hasattr(event, "end_time"):
            if event.end_time <= event.start_time:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # Changed from 400 to 422
                    detail="End time must be after start time",
                )

            if event.start_time < datetime.now():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # Changed from 400 to 422
                    detail="Event dates cannot be in the past",
                )

        # Create event in database
        event_data = event.dict()
        event_data["created_by"] = user_id

        new_event = EventDB(**event_data)
        self.event_repo.add(new_event)

        # Publish message about the created event
        await self._publish_event_message(
            new_event.event_id,
            getattr(new_event, "title", new_event.title),  # Fallback to name if title not available
            "created",
            user_id,
        )

        return new_event
    
    
    async def subscribe_user_to_event(self, event_id: str, user_id: str) -> None:
        """Subscribe a user to an event

        Args:
            event_id: The ID of the event
            user_id: The ID of the user to subscribe
        """
        # Get the event
        event = await self.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found"
            )

        # Subscribe logic here (if applicable)
        # For example, add user to event's subscriber list
        if user_id not in event.subscribers:
            event.subscribers.append(user_id)
            self.event_repo.filter_by(event_id=event_id).update(subscribers=event.subscribers)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_id} is already subscribed to event {event_id}",
            )
        # Publish message about the subscription
        await self._publish_event_message(
            event_id,
            getattr(event, "title", event.title),  # Fallback to name
            "subscribed",
            user_id,
        )


    async def update_event(
        self, event_id: str, updated_event: EventUpdate, user_id: str
    ) -> EventDB:
        """Update an event and publish a notification

        Args:
            event_id: The ID of the event to update
            updated_event: The new event data
            user_id: The ID of the user updating the event

        Returns:
            EventDB: The updated event
        """
        # Get the event
        event = await self.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found"
            )

        # Validate ownership if needed
        # if event.created_by != user_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to update this event"
        #     )

        # Check date validations if dates are being updated
        update_data = updated_event.dict(exclude_unset=True)

        start_time = update_data.get(
            "start_time", event.start_time if hasattr(event, "start_time") else None
        )
        end_time = update_data.get(
            "end_time", event.end_time if hasattr(event, "end_time") else None
        )

        if start_time and end_time and end_time <= start_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="End time must be after start time"
            )

        # Update event in database
        self.event_repo.filter_by(event_id=event_id).update(**update_data)

        # Get updated event
        updated_event_obj = await self.get_event(event_id)

        # Publish message about the updated event
        await self._publish_event_message(
            event_id,
            getattr(updated_event_obj, "title", updated_event_obj.title),  # Fallback to name
            "updated",
            user_id,
        )

        return updated_event_obj

    async def unsubscribe_user_from_event(self, event_id: str, user_id: str) -> None:
        """Unsubscribe a user from an event

        Args:
            event_id: The ID of the event
            user_id: The ID of the user to unsubscribe
        """
        # Get the event
        event = await self.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found"
            )

        # Unsubscribe logic here (if applicable)
        # For example, remove user from event's subscriber list
        if user_id in event.subscribers:
            event.subscribers.remove(user_id)
            self.event_repo.filter_by(event_id=event_id).update(subscribers=event.subscribers)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User {user_id} is not subscribed to event {event_id}",
            )

    async def delete_event(self, event_id: str, user_id: str) -> None:
        """Delete an event and publish a notification

        Args:
            event_id: The ID of the event to delete
            user_id: The ID of the user deleting the event
        """
        # Get the event
        event = await self.get_event(event_id)
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found"
            )

        # Validate ownership if needed
        # if event.created_by != user_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="Not authorized to delete this event"
        #     )

        # Store event title before deletion
        event_title = getattr(event, "title", event.title)  # Fallback to name

        # Delete from database
        self.event_repo.filter_by(event_id=event_id).delete()

        # Publish message about the deleted event
        await self._publish_event_message(event_id, event_title, "deleted", user_id)

    async def close(self) -> None:
        """Close connections to message broker"""
        if self.connection:
            await self.connection.close()
