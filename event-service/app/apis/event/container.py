"""Module to provide the containers with injected services for the app"""

from dependency_injector import containers, providers

from app.apis.event.models import EventDB
from app.apis.event.service import EventService


class EventContainer(containers.DeclarativeContainer):
    """Container to serve the Event service with the configured repository"""

    repository = providers.Dependency()
    # Configure repository to use
    event_repository = providers.Singleton(
        repository,
        model=EventDB,
    )

    # Configure service with repository
    event_service = providers.Singleton(EventService, event_repo=event_repository)
