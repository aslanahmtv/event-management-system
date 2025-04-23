"""Module with the models for the DB connection"""
from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, validator


class EventStatus(str, Enum):
    """Event status options"""

    SCHEDULED = "scheduled"
    CANCELED = "canceled"
    COMPLETED = "completed"


class GeoPoint(BaseModel):
    """Geographical coordinates model"""

    latitude: float
    longitude: float


class Event(BaseModel):
    """Base event model with required and optional fields"""

    # Required fields
    title: str = Field(
        ..., min_length=1, max_length=100, description="Event title (1-100 characters)"
    )
    description: str = Field(..., description="Event description")
    location: str = Field(..., min_length=1, description="Event location")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")

    # Optional fields
    tags: List[str] = Field(default=[], description="Event tags")
    max_attendees: Optional[int] = Field(default=None, description="Maximum number of attendees")
    status: EventStatus = Field(default=EventStatus.SCHEDULED, description="Event status")
    attachment_url: Optional[str] = Field(default=None, description="URL for event attachment")
    coordinates: Optional[GeoPoint] = Field(default=None, description="Event location coordinates")

    @validator("end_time")
    def end_time_must_be_after_start_time(cls, v, values):
        """Validate that end_time is after start_time"""
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

    @validator("start_time")
    def start_time_not_in_past(cls, v):
        """Validate that start_time is not in the past when created"""
        if v < datetime.now():
            raise ValueError("Event dates should not be in the past")
        return v


class EventDB(Event):
    """Event model with additional database fields"""

    __colname__ = "events"
    __id_field__ = "event_id"

    event_id: str = Field(
        default_factory=lambda: uuid4().hex, description="Unique event identifier"
    )
    created_by: str = Field(..., description="User ID of event creator")
    created_at: datetime = Field(
        default_factory=datetime.now, description="Event creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now, description="Event last update timestamp"
    )

    subscribers: List[str] = Field(
        default=[], description="List of user IDs subscribed to event updates"
    )

    class Config:
        """Configuration for the model"""

        schema_extra = {
            "example": {
                "event_id": "123e4567e89b12d3a456426614174000",
                "title": "Tech Conference 2025",
                "description": "Annual technology conference",
                "location": "San Francisco Convention Center",
                "start_time": "2025-05-15T09:00:00",
                "end_time": "2025-05-17T18:00:00",
                "created_by": "user123",
                "created_at": "2025-01-15T14:23:55",
                "updated_at": "2025-01-15T14:23:55",
                "tags": ["technology", "conference", "networking"],
                "max_attendees": 500,
                "status": "scheduled",
                "attachment_url": "https://example.com/event-brochure.pdf",
                "coordinates": {"latitude": 37.7749, "longitude": -122.4194},
                "subscribers": ["user456", "user789"],
            }
        }
