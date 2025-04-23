"""Module with the routers related to the notification service"""
import json
from typing import Dict, List, Optional

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from fastapi.security import OAuth2PasswordBearer

from app.apis.auth.jwt import get_current_user_id
from .models import NotificationDB
from .service import NotificationService
from .connection import connection_manager  # Changed from .websocket import connection_manager
import datetime

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

@inject
def get_notification_router(notification_service: NotificationService = Provide["notification_container.notification_service"]):
    router = APIRouter()

    @router.get(
        "",
        response_model=List[NotificationDB],
        response_description="Get notification history",
        status_code=status.HTTP_200_OK,
        tags=["notifications"],
    )
    async def get_notifications(
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(10, ge=1, le=100, description="Number of notifications per page"),
        token: str = Depends(oauth2_scheme),
    ) -> List[NotificationDB]:
        """
        Retrieve notification history for the current user.

        - **page**: Page number (starting from 1)
        - **page_size**: Number of notifications per page (max 100)
        """
        user_id = get_current_user_id(token)
        notifications = await notification_service.get_user_notifications(
            user_id=user_id,
            page=page,
            page_size=page_size
        )
        return notifications

    @router.get(
        "/count",
        response_model=Dict[str, int],
        response_description="Get unread notification count",
        status_code=status.HTTP_200_OK,
        tags=["notifications"],
    )
    async def get_notification_count(
        token: str = Depends(oauth2_scheme)
    ) -> Dict[str, int]:
        """
        Get the count of unread notifications for the current user.
        """
        user_id = get_current_user_id(token)
        count = await notification_service.get_notification_count(user_id)
        return {"count": count}

    @router.get(
        "/{notification_id}",
        response_model=NotificationDB,
        response_description="Get a single notification",
        status_code=status.HTTP_200_OK,
        tags=["notifications"],
    )
    async def get_notification(
        notification_id: str,
        token: str = Depends(oauth2_scheme)
    ) -> NotificationDB:
        """
        Retrieve a specific notification by ID.

        - **notification_id**: The unique identifier of the notification
        """
        user_id = get_current_user_id(token)
        notification = await notification_service.get_notification(notification_id, user_id)
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )
        return notification

    @router.post(
        "/mark-read/{notification_id}",
        response_description="Mark notification as read",
        status_code=status.HTTP_200_OK,
        tags=["notifications"],
    )
    async def mark_notification_read(
        notification_id: str,
        token: str = Depends(oauth2_scheme)
    ) -> Dict[str, str]:
        """
        Mark a notification as read.

        - **notification_id**: The unique identifier of the notification
        """
        user_id = get_current_user_id(token)
        success = await notification_service.mark_notification_read(notification_id, user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Notification {notification_id} not found",
            )
        return {"status": "success", "message": f"Notification {notification_id} marked as read"}

    @router.post(
        "/mark-all-read",
        response_description="Mark all notifications as read",
        status_code=status.HTTP_200_OK,
        tags=["notifications"],
    )
    async def mark_all_notifications_read(
        token: str = Depends(oauth2_scheme)
    ) -> Dict[str, str]:
        """
        Mark all notifications as read for the current user.
        """
        user_id = get_current_user_id(token)
        count = await notification_service.mark_all_notifications_read(user_id)
        return {"status": "success", "message": f"Marked {count} notifications as read"}

    return router


@inject
def get_websocket_router():
    router = APIRouter()

    @router.websocket("")
    async def websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
        """
        WebSocket endpoint for real-time notifications
        
        Connect to this endpoint to receive real-time notifications.
        Pass a valid JWT token as a query parameter 'token'.
        
        Example: ws://localhost:8081/ws?token=your_jwt_token
        
        The client can send messages to:
        - Subscribe to events: {"action": "subscribe", "event_id": "123"}
        - Unsubscribe from events: {"action": "unsubscribe", "event_id": "123"}
        """
        # Connect the client
        user_id = await connection_manager.connect(websocket, token)
        
        if not user_id:
            return  # Connection was rejected due to invalid token
        
        try:
            # Message handling loop
            while True:
                # Wait for messages from the client
                message = await websocket.receive_text()
                
                try:
                    data = json.loads(message)
                    
                    # Handle subscription request
                    if data.get("action") == "subscribe" and "event_id" in data:
                        event_id = data["event_id"]
                        await connection_manager.subscribe_to_event(user_id, event_id)
                        await websocket.send_json({
                            "type": "subscription_update",
                            "event_id": event_id,
                            "status": "subscribed"
                        })
                    
                    # Handle unsubscription request
                    elif data.get("action") == "unsubscribe" and "event_id" in data:
                        event_id = data["event_id"]
                        await connection_manager.unsubscribe_from_event(user_id, event_id)
                        await websocket.send_json({
                            "type": "subscription_update",
                            "event_id": event_id,
                            "status": "unsubscribed"
                        })
                    
                    # Handle ping request
                    elif data.get("action") == "ping":
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": str(datetime.now().isoformat())
                        })
                
                except json.JSONDecodeError:
                    # Ignore invalid JSON
                    pass
                
        except WebSocketDisconnect:
            # Client disconnected
            await connection_manager.disconnect(websocket, user_id)
    
    return router

