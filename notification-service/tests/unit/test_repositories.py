"""Unit testing for app.apis.event.repositories"""

from app.apis.notification.models import NotificationDB
from app.apis.repositories import get_repository, str_to_class
from redbird.repos import MemoryRepo


def test_str_to_class():
    assert str_to_class("MemoryRepo") == MemoryRepo
    assert str_to_class("NotExistingClass") is None
    assert str_to_class("BaseModel") is None  # Only valid repositories


def test_get_repository():
    assert isinstance(
        get_repository("MemoryRepo", id_field="notification_id", model=NotificationDB),
        MemoryRepo,
    )
    assert get_repository("not_supported_db", "notification_id", NotificationDB) is None
