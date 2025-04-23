"""Module with the models for the auth DB connection"""
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field, EmailStr


class UserRole(str, Enum):
    """User role options"""
    USER = "user"
    ADMIN = "admin"


class User(BaseModel):
    """Base user model with required fields"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username for login")
    full_name: Optional[str] = Field(None, description="User's full name")


class UserDB(User):
    """User model with additional database fields"""
    __colname__ = "users"
    __id_field__ = "user_id"

    user_id: str = Field(default_factory=lambda: uuid4().hex, description="Unique user identifier")
    password_hash: str = Field(..., description="Hashed password")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    is_active: bool = Field(default=True, description="Whether account is active")
    created_at: datetime = Field(default_factory=datetime.now, description="Account creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    role: UserRole = Field(default=UserRole.USER, description="User role")
    
    class Config:
        """Configuration for the model"""
        schema_extra = {
            "example": {
                "user_id": "123e4567e89b12d3a456426614174000",
                "email": "user@example.com",
                "username": "example_user",
                "full_name": "Example User",
                "password_hash": "$2b$12$...",
                "is_verified": False,
                "is_active": True,
                "created_at": "2025-04-23T12:00:00",
                "updated_at": "2025-04-23T12:00:00",
                "last_login": None,
                "role": "user"
            }
        }