"""Module to provide the containers with injected services for the app"""

from dependency_injector import containers, providers

from app.apis.user.routers import get_user_router, get_auth_router
from app.apis.user.container import AuthContainer, UserContainer

from app.apis.repositories import get_repository

from .config import settings


class AppContainer(containers.DeclarativeContainer):
    """Container to serve all the containers related to the app"""

    # Set wiring between endpoints and injected repositories
    wiring_config = containers.WiringConfiguration(
        modules=[get_user_router, get_auth_router]
    )

    # Setup common repository factory
    repository = providers.Singleton(get_repository, settings.REPOSITORY_NAME)

    # User container (legacy)
    user_container = providers.Container(
        UserContainer,
        repository=repository,
    )
    
    # Auth container
    auth_container = providers.Container(
        AuthContainer,
        repository=repository,
    )