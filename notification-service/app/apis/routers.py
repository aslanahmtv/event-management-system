"""Module for including all the app's routers"""
from fastapi import APIRouter

from app.apis.notification.routers import get_notification_router
from app.apis.notification.routers import get_websocket_router

def get_app_router():
    router = APIRouter()
    router.include_router(get_notification_router(), prefix="/notifications", tags=["notifications"])
    router.include_router(get_websocket_router(), prefix="/ws", tags=["websocket"])
    
    return router