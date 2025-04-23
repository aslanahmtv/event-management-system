"""Module with schemas for transforming data from requests and responses"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any

from pydantic import BaseModel, Field, validator


class NotificationType(str, Enum):
    """Enum for notification types"""
    EVENT_CREATED = "event.created"
    EVENT_UPDATED = "event.updated"
    EVENT_DELETED = "event.deleted"
    EVENT_SUBSCRIBED = "event.subscribed"
    EVENT_UNSUBSCRIBED = "event.unsubscribed"
    

class EventNotificationData(BaseModel):
    """Schema for event data in notifications"""
    id: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    action: str = Field(..., description="Action performed on the event (created/updated/deleted)")
    timestamp: str = Field(..., description="ISO datetime string of when the action occurred")
    

class NotificationCreate(BaseModel):
    """Schema for creating a new notification"""
    type: str = Field("notification", const=True, description="Type of message")
    notification_type: NotificationType = Field(..., description="Type of notification")
    event: EventNotificationData = Field(..., description="Event data")
    user: str = Field(..., description="User who performed the action")
    delivered_to: List[str] = Field(default_factory=list, description="List of users this notification was delivered to")
    read_by: List[str] = Field(default_factory=list, description="List of users who have read this notification")
    

class NotificationResponse(BaseModel):
    """Schema for responding with notification data"""
    notification_id: str = Field(..., description="Unique notification identifier")
    type: str = Field(..., description="Type of message")
    notification_type: NotificationType = Field(..., description="Type of notification")
    event: EventNotificationData = Field(..., description="Event data")
    user: str = Field(..., description="User who performed the action")
    timestamp: datetime = Field(..., description="Notification creation timestamp")
    delivered_to: List[str] = Field(..., description="List of users this notification was delivered to")
    read_by: List[str] = Field(default_factory=list, description="List of users who have read this notification")
    
    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "notification_id": "123e4567e89b12d3a456426614174000",
                "type": "notification",
                "notification_type": "event.created",
                "event": {
                    "id": "456e4567e89b12d3a456426614174123",
                    "title": "Tech Conference 2025",
                    "action": "created",
                    "timestamp": "2025-01-15T14:23:55"
                },
                "user": "user123",
                "timestamp": "2025-01-15T14:23:55",
                "delivered_to": ["user456", "user789"],
                "read_by": ["user456"]
            }
        }


class NotificationList(BaseModel):
    """Schema for returning a list of notifications"""
    notifications: List[NotificationResponse]
    total: int = Field(..., description="Total number of notifications")
    page: int = Field(1, description="Current page number")
    page_size: int = Field(..., description="Number of notifications per page")


class WebSocketSubscribe(BaseModel):
    """Schema for WebSocket subscription requests"""
    action: str = Field("subscribe", const=True, description="Action to perform")
    event_id: str = Field(..., description="Event ID to subscribe to")


class WebSocketUnsubscribe(BaseModel):
    """Schema for WebSocket unsubscription requests"""
    action: str = Field("unsubscribe", const=True, description="Action to perform")
    event_id: str = Field(..., description="Event ID to unsubscribe from")


class WebSocketPing(BaseModel):
    """Schema for WebSocket ping requests"""
    action: str = Field("ping", const=True, description="Action to perform")


class WebSocketSubscriptionUpdate(BaseModel):
    """Schema for WebSocket subscription update responses"""
    type: str = Field("subscription_update", const=True, description="Type of message")
    event_id: str = Field(..., description="Event ID")
    status: str = Field(..., description="Subscription status (subscribed/unsubscribed)")


class WebSocketPong(BaseModel):
    """Schema for WebSocket pong responses"""
    type: str = Field("pong", const=True, description="Type of message")
    timestamp: str = Field(..., description="ISO datetime string of server time")


class NotificationStatusUpdate(BaseModel):
    """Schema for notification status updates"""
    status: str = Field(..., description="Status of the operation")
    message: str = Field(..., description="Operation result message")


class NotificationCount(BaseModel):
    """Schema for notification count responses"""
    count: int = Field(..., description="Number of unread notifications")