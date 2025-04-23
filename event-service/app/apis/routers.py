"""Module for including all the app's routers"""
from fastapi import APIRouter

from app.apis.event.routers import get_event_router


def get_app_router():
    router = APIRouter()
    router.include_router(get_event_router(), prefix="/events", tags=["events"])

    return router
