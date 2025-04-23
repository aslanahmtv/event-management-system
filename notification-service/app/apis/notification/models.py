"""Module with the models for the DB connection"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Notification type options"""
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"


class Notification(BaseModel):
    """Base notification model"""
    type: str = Field(default="notification", description="Notification type")
    notification_type: NotificationType = Field(..., description="Event notification type")
    event: Dict[str, Any] = Field(..., description="Event data")
    user: str = Field(..., description="User who performed the action")


class NotificationDB(Notification):
    """Notification model with additional database fields"""
    __colname__ = "notifications"
    __id_field__ = "notification_id"

    notification_id: str = Field(default_factory=lambda: uuid4().hex, description="Unique notification identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Notification timestamp")
    delivered_to: List[str] = Field(default=[], description="List of user IDs this notification was delivered to")
    read_by: List[str] = Field(default_factory=list)
    
    class Config:
        """Configuration for the model"""
        schema_extra = {
            "example": {
                "notification_id": "123e4567e89b12d3a456426614174001",
                "type": "notification",
                "notification_type": "event.created",
                "event": {
                    "id": "123e4567e89b12d3a456426614174000",
                    "title": "Tech Conference 2025",
                    "action": "created",
                    "timestamp": "2025-01-15T14:23:55"
                },
                "user": "user123",
                "timestamp": "2025-01-15T14:23:55",
                "delivered_to": ["user456", "user789"]
            }
        }


class WebSocketConnection(BaseModel):
    """Model to track active WebSocket connections"""
    user_id: str
    connection_id: str = Field(default_factory=lambda: uuid4().hex)
    connected_at: datetime = Field(default_factory=datetime.now)
    subscribed_events: List[str] = Field(default=[])