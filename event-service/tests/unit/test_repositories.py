"""Unit testing for app.apis.event.repositories"""

from app.apis.event.models import EventDB
from app.apis.repositories import get_repository, str_to_class
from redbird.repos import MemoryRepo


def test_str_to_class():
    assert str_to_class("MemoryRepo") == MemoryRepo
    assert str_to_class("NotExistingClass") is None
    assert str_to_class("BaseModel") is None  # Only valid repositories


def test_get_repository():
    assert isinstance(
        get_repository("MemoryRepo", id_field="event_id", model=EventDB),
        MemoryRepo,
    )
    assert get_repository("not_supported_db", "event_id", EventDB) is None
