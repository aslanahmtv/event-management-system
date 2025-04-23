"""Module for including all the app's routers"""
from fastapi import APIRouter

from app.apis.config import settings
from app.apis.user.routers import get_auth_router, get_user_router


"""Module for including all the app's routers"""
from fastapi import APIRouter

from app.apis.config import settings
from app.apis.user.routers import get_auth_router, get_user_router

def get_app_router():
    router = APIRouter()
    
    # Auth endpoints
    router.include_router(
        get_auth_router(), 
        prefix=f"/auth", 
        tags=["authentication"]
    )
    
    # User endpoints
    router.include_router(
        get_user_router(), 
        prefix=f"/users", 
        tags=["users"]
    )
    
    return router
    