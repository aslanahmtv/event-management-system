"""Module with the Auth service implementation"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Union, List

from fastapi import HTTPException, status
from redbird.templates import TemplateRepo

from app.apis.user.security import hash_password, verify_password, create_access_token
from app.apis.user.models import UserDB
from app.apis.user.schemas import UserRegister, UserLogin, Token
from app.apis.config import settings


class AuthService:
    """Service to handle authentication operations

    Args:
        user_repo (TemplateRepo): Repository for the user DB connection
    """

    def __init__(self, user_repo: TemplateRepo) -> None:
        self.user_repo = user_repo

    async def register_user(self, user_data: UserRegister) -> UserDB:
        """Register a new user

        Args:
            user_data: User registration data

        Returns:
            UserDB: Created user

        Raises:
            HTTPException: If username or email already exists
        """
        # Check if username already exists
        existing_user = self.user_repo.filter_by(username=user_data.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )

        # Check if email already exists
        existing_email = self.user_repo.filter_by(email=user_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Create new user with hashed password
        password_hash = hash_password(user_data.password)
        
        user_dict = user_data.dict(exclude={"password"})
        user_dict["password_hash"] = password_hash
        
        new_user = UserDB(**user_dict)
        self.user_repo.add(new_user)
        
        return new_user

    async def login_user(self, login_data: UserLogin) -> Dict[str, Any]:
        """Login a user and return access token

        Args:
            login_data: Login credentials

        Returns:
            Dict containing user and token information

        Raises:
            HTTPException: If login fails
        """
        # Check if login is with email or username
        is_email = "@" in login_data.username_or_email
        
        if is_email:
            user = self.user_repo.filter_by(email=login_data.username_or_email).first()
        else:
            user = self.user_repo.filter_by(username=login_data.username_or_email).first()
            
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        # Update last login
        now = datetime.now()
        self.user_repo.filter_by(user_id=user.user_id).update(
            last_login=now,
            updated_at=now
        )
        
        # Create access token
        token_data = {
            "sub": user.user_id,
            "role": user.role
        }
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(token_data, expires_delta)
        
        return {
            "user": user,
            "token": {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
            }
        }
        
    async def get_user_by_id(self, user_id: str) -> Optional[UserDB]:
        """Get a user by ID

        Args:
            user_id: User ID

        Returns:
            UserDB or None if not found
        """
        return self.user_repo.filter_by(user_id=user_id).first()

    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        """Get a user by email

        Args:
            email: User email

        Returns:
            UserDB or None if not found
        """
        return self.user_repo.filter_by(email=email).first()

    async def get_user_by_username(self, username: str) -> Optional[UserDB]:
        """Get a user by username

        Args:
            username: Username

        Returns:
            UserDB or None if not found
        """
        return self.user_repo.filter_by(username=username).first()
    


class UserService:
    """Service to handle user management operations

    Args:
        user_repo (TemplateRepo): Repository for the user DB connection
    """

    def __init__(self, user_repo: TemplateRepo) -> None:
        self.user_repo = user_repo

    async def get_user_by_id(self, user_id: str) -> Optional[UserDB]:
        """Get a user by ID

        Args:
            user_id: User ID

        Returns:
            UserDB or None if not found
        """
        return self.user_repo.filter_by(user_id=user_id).first()

    async def get_user_by_email(self, email: str) -> Optional[UserDB]:
        """Get a user by email

        Args:
            email: User email

        Returns:
            UserDB or None if not found
        """
        return self.user_repo.filter_by(email=email).first()

    async def get_user_by_username(self, username: str) -> Optional[UserDB]:
        """Get a user by username

        Args:
            username: Username

        Returns:
            UserDB or None if not found
        """
        return self.user_repo.filter_by(username=username).first()
        
    async def get_users(self, page: int = 1, page_size: int = 10) -> List[UserDB]:
        """Get a paginated list of users
        
        Args:
            page: Page number (starting from 1)
            page_size: Number of users per page
            
        Returns:
            List of users for the requested page
        """
        users = self.user_repo.filter_by().all()
        
        # Sort by created_at
        users.sort(key=lambda u: getattr(u, "created_at", datetime.max), reverse=True)
        
        # Apply pagination
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        
        return users[start_idx:end_idx]
    
    async def count_users(self) -> int:
        """Get the total count of users
        
        Returns:
            Total number of users
        """
        return len(self.user_repo.filter_by().all())
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[UserDB]:
        """Update user information
        
        Args:
            user_id: ID of the user to update
            update_data: Dictionary of fields to update
            
        Returns:
            Updated user or None if not found
            
        Raises:
            HTTPException: If trying to update username or email to one that already exists
        """
        # Check if user exists
        user = self.user_repo.filter_by(user_id=user_id).first()
        if not user:
            return None
            
        # Check if updating username and if it already exists
        if "username" in update_data and update_data["username"] != user.username:
            existing = self.user_repo.filter_by(username=update_data["username"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
                
        # Check if updating email and if it already exists
        if "email" in update_data and update_data["email"] != user.email:
            existing = self.user_repo.filter_by(email=update_data["email"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already registered"
                )
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.now()
        
        # Update user
        self.user_repo.filter_by(user_id=user_id).update(**update_data)
        
        # Return updated user
        return self.user_repo.filter_by(user_id=user_id).first()
    
    async def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account
        
        Args:
            user_id: ID of the user to deactivate
            
        Returns:
            True if successful, False if user not found
        """
        user = self.user_repo.filter_by(user_id=user_id).first()
        if not user:
            return False
            
        self.user_repo.filter_by(user_id=user_id).update(
            is_active=False,
            updated_at=datetime.now()
        )
        
        return True
    
    async def activate_user(self, user_id: str) -> bool:
        """Activate a user account
        
        Args:
            user_id: ID of the user to activate
            
        Returns:
            True if successful, False if user not found
        """
        user = self.user_repo.filter_by(user_id=user_id).first()
        if not user:
            return False
            
        self.user_repo.filter_by(user_id=user_id).update(
            is_active=True,
            updated_at=datetime.now()
        )
        
        return True
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user account
        
        Args:
            user_id: ID of the user to delete
            
        Returns:
            True if successful, False if user not found
        """
        user = self.user_repo.filter_by(user_id=user_id).first()
        if not user:
            return False
            
        self.user_repo.delete(user)
        return True