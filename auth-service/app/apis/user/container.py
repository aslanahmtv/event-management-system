"""Module to provide the containers with injected services for auth"""
from dependency_injector import containers, providers

from app.apis.user.models import UserDB
from app.apis.user.service import AuthService, UserService


class UserContainer(containers.DeclarativeContainer):
    """Container to serve the User service with the configured repository"""

    repository = providers.Dependency()
    
    # Configure repository to use
    user_repository = providers.Singleton(
        repository,
        model=UserDB,
    )

    # Configure service with repository
    user_service = providers.Singleton(
        UserService, 
        user_repo=user_repository
    )

class AuthContainer(containers.DeclarativeContainer):
    """Container to serve the Auth service with the configured repository"""

    repository = providers.Dependency()
    
    # Configure repository to use
    user_repository = providers.Singleton(
        repository,
        model=UserDB,
    )

    # Configure service with repository
    auth_service = providers.Singleton(
        AuthService, 
        user_repo=user_repository
    )