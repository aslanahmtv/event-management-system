"""Module with schemas for auth requests and responses"""
import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, EmailStr, validator

from .models import UserRole


class UserRegister(BaseModel):
    """Schema for user registration"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username (3-50 chars)")
    password: str = Field(..., min_length=8, description="Password (min 8 chars)")
    full_name: Optional[str] = Field(None, description="User's full name")
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not re.match(r'^[a-zA-Z0-9_]{3,50}$', v):
            raise ValueError('Username must be 3-50 alphanumeric characters or underscores')
        return v
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[0-9]', v):
            raise ValueError('Password must contain at least one number')
        if not re.search(r'[^a-zA-Z0-9]', v):
            raise ValueError('Password must contain at least one special character')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    username_or_email: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")


class TokenData(BaseModel):
    """Schema for JWT token data"""
    sub: str = Field(..., description="Subject (user_id)")
    exp: datetime = Field(..., description="Expiration time")
    iat: datetime = Field(..., description="Issued at time")
    role: UserRole = Field(..., description="User role")


class Token(BaseModel):
    """Schema for token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time in seconds")


class UserResponse(BaseModel):
    """Schema for user data response"""
    user_id: str = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., description="Username")
    full_name: Optional[str] = Field(None, description="User's full name")
    is_verified: bool = Field(..., description="Whether email is verified")
    created_at: datetime = Field(..., description="Account creation timestamp")
    
    class Config:
        """Configuration for the schema"""
        schema_extra = {
            "example": {
                "user_id": "123e4567e89b12d3a456426614174000",
                "email": "user@example.com",
                "username": "example_user",
                "full_name": "Example User",
                "is_verified": False,
                "created_at": "2025-04-23T12:00:00"
            }
        }