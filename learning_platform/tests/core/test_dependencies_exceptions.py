import pytest
from src.core.dependencies import get_storage_service
from src.core.service import StorageService
from src.core.exceptions import FileTooLarge

def test_get_storage_service():
    service = get_storage_service()
    assert isinstance(service, StorageService)

def test_file_too_large_exception():
    exc = FileTooLarge(1048576) # 1 MB
    assert "1 MB" in str(exc)
