"""Module with schemas for transforming data from requests and responses"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator

from app.core.model_factory import optional_model

from .models import EventStatus, GeoPoint


class EventCreate(BaseModel):
    """Schema for creating a new event"""

    title: str = Field(
        ..., min_length=1, max_length=100, description="Event title (1-100 characters)"
    )
    description: str = Field(..., description="Event description")
    location: str = Field(..., min_length=1, description="Event location")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")

    # Optional fields
    tags: Optional[List[str]] = Field(default=[], description="Event tags")
    max_attendees: Optional[int] = Field(default=None, description="Maximum number of attendees")
    status: Optional[EventStatus] = Field(default=EventStatus.SCHEDULED, description="Event status")
    attachment_url: Optional[str] = Field(default=None, description="URL for event attachment")
    coordinates: Optional[GeoPoint] = Field(default=None, description="Event location coordinates")

    @validator("end_time")
    def end_time_must_be_after_start_time(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("End time must be after start time")
        return v

    @validator("start_time")
    def start_time_not_in_past(cls, v):
        if v < datetime.now():
            raise ValueError("Event dates should not be in the past")
        return v


@optional_model
class EventUpdate(BaseModel):
    """Schema for updating an existing event (all fields optional)"""

    title: Optional[str] = Field(
        None, min_length=1, max_length=100, description="Event title (1-100 characters)"
    )
    description: Optional[str] = Field(None, description="Event description")
    location: Optional[str] = Field(None, min_length=1, description="Event location")
    start_time: Optional[datetime] = Field(None, description="Event start time")
    end_time: Optional[datetime] = Field(None, description="Event end time")
    tags: Optional[List[str]] = Field(None, description="Event tags")
    max_attendees: Optional[int] = Field(None, description="Maximum number of attendees")
    status: Optional[EventStatus] = Field(None, description="Event status")
    attachment_url: Optional[str] = Field(None, description="URL for event attachment")
    coordinates: Optional[GeoPoint] = Field(None, description="Event location coordinates")

    # Custom validator for conditional validation of end_time vs start_time
    @validator("end_time")
    def validate_end_time(cls, v, values):
        if v is not None and "start_time" in values and values["start_time"] is not None:
            if v <= values["start_time"]:
                raise ValueError("End time must be after start time")
        return v


class EventResponse(BaseModel):
    """Schema for responding with event data"""

    event_id: str = Field(..., description="Unique event identifier")
    title: str = Field(..., description="Event title")
    description: str = Field(..., description="Event description")
    location: str = Field(..., description="Event location")
    start_time: datetime = Field(..., description="Event start time")
    end_time: datetime = Field(..., description="Event end time")
    created_by: str = Field(..., description="User ID of event creator")
    created_at: datetime = Field(..., description="Event creation timestamp")
    updated_at: datetime = Field(..., description="Event last update timestamp")

    # Optional fields
    tags: List[str] = Field(default=[], description="Event tags")
    max_attendees: Optional[int] = Field(default=None, description="Maximum number of attendees")
    status: EventStatus = Field(default=EventStatus.SCHEDULED, description="Event status")
    attachment_url: Optional[str] = Field(default=None, description="URL for event attachment")
    coordinates: Optional[GeoPoint] = Field(default=None, description="Event location coordinates")
        
    @classmethod
    def from_event_db(cls, event_db):
        """Convert an EventDB object to an EventResponse object"""
        return cls(
            event_id=event_db.event_id,
            title=event_db.title,
            description=event_db.description,
            location=event_db.location,
            start_time=event_db.start_time,
            end_time=event_db.end_time,
            created_by=event_db.created_by,
            created_at=event_db.created_at,
            updated_at=event_db.updated_at,
            tags=event_db.tags,
            max_attendees=event_db.max_attendees,
            status=event_db.status,
            attachment_url=event_db.attachment_url,
            coordinates=event_db.coordinates
        )
    
    class Config:
        orm_mode = True
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
            }
        }


# Additional schemas for specific operations
class EventSubscription(BaseModel):
    """Schema for subscribing to event updates"""

    event_id: str = Field(..., description="Event ID to subscribe to")


class EventList(BaseModel):
    """Schema for returning a list of events"""

    events: List[EventResponse]
    total: int = Field(..., description="Total number of events")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(..., description="Number of events per page")
