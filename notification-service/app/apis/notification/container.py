"""Dependency injection containers"""
from dependency_injector import containers, providers

from app.apis.config import settings
from app.apis.repositories import get_repository


class NotificationContainer(containers.DeclarativeContainer):
    """Container for notification dependencies"""
    
    notification_repository = providers.Singleton(
        get_repository,
        repo_type=settings.REPOSITORY_NAME,
        collection_name="notifications"
    )
