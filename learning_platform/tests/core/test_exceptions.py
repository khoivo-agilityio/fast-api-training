import pytest
from src.core.exceptions import StorageObjectNotFound

def test_storage_object_not_found():
    exc = StorageObjectNotFound("avatars/test.jpg")
    assert "avatars/test.jpg" in str(exc)
