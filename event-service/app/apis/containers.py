"""Module to provide the containers with injected services for the app"""

from dependency_injector import containers, providers

from app.apis.event import routers as event_router
from app.apis.event.container import EventContainer
from app.apis.repositories import get_repository

from .config import settings


class AppContainer(containers.DeclarativeContainer):
    """Container to serve all the containers related to the app"""

    # Set wiring between endpoints and injected repositories
    wiring_config = containers.WiringConfiguration(modules=[event_router])

    # Setup container for event services
    repository = providers.Singleton(get_repository, settings.REPOSITORY_NAME)

    event_container = providers.Container(
        EventContainer,
        repository=repository,
    )
