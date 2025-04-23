"""Unit testing for app.apis.user.repositories"""

from app.apis.user.models import UserDB
from app.apis.repositories import get_repository, str_to_class
from redbird.repos import MemoryRepo


def test_str_to_class():
    assert str_to_class("MemoryRepo") == MemoryRepo
    assert str_to_class("NotExistingClass") is None
    assert str_to_class("BaseModel") is None  # Only valid repositories


def test_get_repository():
    assert isinstance(
        get_repository("MemoryRepo", id_field="user_id", model=UserDB),
        MemoryRepo,
    )
    assert get_repository("not_supported_db", "user_id", UserDB) is None
