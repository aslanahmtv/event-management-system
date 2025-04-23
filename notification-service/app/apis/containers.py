"""Module to provide the containers with injected services for the app"""

from dependency_injector import containers, providers

from app.apis.notification import routers as notification_router
from app.apis.notification.service import NotificationService
from app.apis.notification.models import NotificationDB
from app.apis.repositories import get_repository

from .config import settings


class NotificationContainer(containers.DeclarativeContainer):
    """Container for notification dependencies"""
    
    repository = providers.Dependency()
    
    # Configure repository to use
    notification_repository = providers.Singleton(
        repository,
        model=NotificationDB,
    )
    
    # Configure service with repository
    notification_service = providers.Singleton(
        NotificationService,
        notification_repo=notification_repository
    )


class AppContainer(containers.DeclarativeContainer):
    """Container to serve all the containers related to the app"""

    # Set wiring between endpoints and injected repositories
    wiring_config = containers.WiringConfiguration(
        modules=["app.apis.notification.routers"]
    )

    # Setup repository factory
    repository = providers.Singleton(get_repository, settings.REPOSITORY_NAME)

    # Notification container
    notification_container = providers.Container(
        NotificationContainer,
        repository=repository,
    )