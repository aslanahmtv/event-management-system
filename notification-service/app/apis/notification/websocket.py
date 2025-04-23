"""WebSocket routing for notification service"""
import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .connection import connection_manager  # Import from the new module

def get_websocket_router():
    """Get WebSocket router"""
    router = APIRouter()
    
    @router.websocket("/ws")
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