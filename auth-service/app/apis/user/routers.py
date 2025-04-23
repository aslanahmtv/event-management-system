"""Module with the routers related to authentication"""
from typing import Dict, Any

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Body, Depends, Request, HTTPException, status

from .rate_limiter import rate_limit_login
from .security import get_current_user
from .schemas import UserRegister, UserLogin, UserResponse, Token
from .service import AuthService


@inject
def get_auth_router(auth_service: AuthService = Provide["auth_container.auth_service"]):
    router = APIRouter()

    @router.post(
        "/register",
        response_model=UserResponse,
        status_code=status.HTTP_201_CREATED,
        tags=["authentication"],
    )
    async def register(user_data: UserRegister = Body(...)) -> UserResponse:
        """
        Register a new user.
        
        - **email**: Valid email address
        - **username**: 3-50 alphanumeric characters or underscores
        - **password**: Minimum 8 characters, at least one uppercase letter, one number, one special character
        - **full_name**: Optional full name
        """
        user = await auth_service.register_user(user_data)
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_verified=user.is_verified,
            created_at=user.created_at
        )

    @router.post(
        "/login",
        response_model=Token,
        tags=["authentication"],
    )
    async def login(
        request: Request,
        login_data: UserLogin = Body(...)
    ) -> Token:
        """
        Login and get access token.
        
        - **username_or_email**: Username or email address
        - **password**: Password
        
        Returns a JWT token that can be used to authenticate API requests.
        """
        # Apply rate limiting
        rate_limit_login(request)
        
        # Process login
        result = await auth_service.login_user(login_data)
        return result["token"]

    @router.get(
        "/me",
        response_model=UserResponse,
        tags=["authentication"],
    )
    async def get_current_user_info(user_id: str = Depends(get_current_user)) -> UserResponse:
        """
        Get information about the currently logged-in user.
        
        Requires authentication with a valid JWT token.
        """
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
            
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_verified=user.is_verified,
            created_at=user.created_at
        )

    return router


@inject
def get_user_router(auth_service: AuthService = Provide["auth_container.auth_service"]):
    router = APIRouter()

    @router.get(
        "/{user_id}",
        response_model=UserResponse,
        tags=["users"],
    )
    async def get_user(
        user_id: str,
        current_user_id: str = Depends(get_current_user)
    ) -> UserResponse:
        """
        Get information about a specific user.
        
        Requires authentication with a valid JWT token.
        """
        user = await auth_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )
            
        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            is_verified=user.is_verified,
            created_at=user.created_at
        )

    return router