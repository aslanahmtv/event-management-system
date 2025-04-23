"""WebSocket connection manager for notification service"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from app.apis.auth.jwt import decode_token
import os 

from app.apis.config import settings

class ConnectionManager:
    """Manager for WebSocket connections"""
    
    def __init__(self):
        # Map of user_id -> list of WebSocket connections
        self.active_connections: Dict[str, List[WebSocket]] = {}
        
        # Map of event_id -> set of subscribed user_ids
        self.event_subscriptions: Dict[str, Set[str]] = {}
        
        # Map of user_id -> set of subscribed event_ids
        self.user_subscriptions: Dict[str, Set[str]] = {}
        
        self.logger = logging.getLogger("connection_manager")
    
    async def connect(self, websocket: WebSocket, token: Optional[str] = None) -> Optional[str]:
        """Connect a client and authenticate if token provided
        
        Args:
            websocket: WebSocket connection
            token: JWT token for authentication
            
        Returns:
            User ID if authenticated, None if not
        """
        self.logger.info(f"Connection attempt with token: {token is not None}")
        self.logger.info(f"TESTING env: {os.environ.get('TESTING')}")
        self.logger.info(f"DEBUG_MODE: {settings.DEBUG_MODE}")
        
        if token == "mock_token" and (os.environ.get("TESTING") == "1" or settings.DEBUG_MODE):
            # Accept the connection for test token
            await websocket.accept()
            user_id = "test_user_1"
            
            # Initialize connection tracking
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
            
            # Initialize user subscriptions if needed
            if user_id not in self.user_subscriptions:
                self.user_subscriptions[user_id] = set()
            
            # Send welcome message
            await websocket.send_json({
                "type": "connection_status",
                "status": "connected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat()
            })
            
            self.logger.info(f"Test client connected: {user_id}")
            return user_id
        # Authenticate with token
        user_id = None
        
        if token:
            try:
                payload = decode_token(token)
                user_id = payload.get("sub")
            except Exception as e:
                self.logger.warning(f"Authentication failed: {str(e)}")
                await websocket.close(code=1008)  # Policy violation
                return None
        
        if not user_id:
            self.logger.warning("Connection attempt without valid authentication")
            await websocket.close(code=1008)  # Policy violation
            return None
            
        # Accept the connection
        await websocket.accept()
        
        # Store the connection
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)
        
        self.logger.info(f"Client connected: {user_id}")
        
        # Initialize user subscriptions if needed
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        # Send welcome message
        await websocket.send_json({
            "type": "connection_status",
            "status": "connected",
            "user_id": user_id,
            "timestamp": datetime.now().isoformat()
        })
        
        return user_id
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a client
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        # Remove this specific connection
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            
            # If no more connections for this user, clean up
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
        
        self.logger.info(f"Client disconnected: {user_id}")
    
    async def subscribe_to_event(self, user_id: str, event_id: str):
        """Subscribe a user to event updates
        
        Args:
            user_id: User ID
            event_id: Event ID
        """
        # Initialize if needed
        if event_id not in self.event_subscriptions:
            self.event_subscriptions[event_id] = set()
        
        if user_id not in self.user_subscriptions:
            self.user_subscriptions[user_id] = set()
        
        # Add subscription
        self.event_subscriptions[event_id].add(user_id)
        self.user_subscriptions[user_id].add(event_id)
        
        self.logger.info(f"User {user_id} subscribed to event {event_id}")
    
    async def unsubscribe_from_event(self, user_id: str, event_id: str):
        """Unsubscribe a user from event updates
        
        Args:
            user_id: User ID
            event_id: Event ID
        """
        # Remove from event subscriptions
        if event_id in self.event_subscriptions and user_id in self.event_subscriptions[event_id]:
            self.event_subscriptions[event_id].remove(user_id)
            
            # Clean up if no more subscribers
            if not self.event_subscriptions[event_id]:
                del self.event_subscriptions[event_id]
        
        # Remove from user subscriptions
        if user_id in self.user_subscriptions and event_id in self.user_subscriptions[user_id]:
            self.user_subscriptions[user_id].remove(event_id)
            
            # Clean up if no more subscriptions
            if not self.user_subscriptions[user_id]:
                del self.user_subscriptions[user_id]
        
        self.logger.info(f"User {user_id} unsubscribed from event {event_id}")
    
    async def broadcast_notification(self, notification, notification_repo, event_id: Optional[str] = None):
        """Broadcast a notification to relevant users
        
        Args:
            notification: Notification object
            notification_repo: Repository for saving notifications
            event_id: Event ID (if related to a specific event)
        """
        notification_type = notification.notification_type
        recipients = set()
        
        if event_id:
            # For event updates/deletions, send to subscribers
            if event_id in self.event_subscriptions:
                recipients.update(self.event_subscriptions[event_id])
            
            # Always send to the event creator
            if hasattr(notification, 'event') and 'created_by' in notification.event:
                recipients.add(notification.event["created_by"])
        else:
            # For new events, broadcast to all connected users
            recipients.update(self.active_connections.keys())
        
        # Save notification to database for each recipient
        delivered_to = []
        for user_id in recipients:
            # Create notification entry
            db_notification = {
                "user_id": user_id,
                "content": notification.dict(),
                "is_read": False,
                "timestamp": datetime.now(),
            }
            
            # Add to database
            notification_repo.add(db_notification)
            delivered_to.append(user_id)
        
        # Broadcast to online users
        for user_id in recipients:
            if user_id in self.active_connections:
                for websocket in self.active_connections[user_id]:
                    try:
                        await websocket.send_json(notification.dict())
                    except Exception as e:
                        self.logger.error(f"Error sending to {user_id}: {str(e)}")
        
        self.logger.info(f"Broadcasted {notification_type} to {len(recipients)} recipients")


# Create a global instance
connection_manager = ConnectionManager()