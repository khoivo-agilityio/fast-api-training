import pytest
from unittest.mock import patch, MagicMock
from src.core.database import _normalize_db_url, get_db

def test_normalize_db_url():
    url = "postgresql://user:pass@localhost:5432/db"
    assert _normalize_db_url(url) == "postgresql+asyncpg://user:pass@localhost:5432/db"

    url2 = "sqlite:///:memory:"
    assert _normalize_db_url(url2) == url2

@pytest.mark.asyncio
async def test_get_db():
    with patch("src.core.database.async_session_factory") as mock_factory:
        mock_session = MagicMock()
        mock_factory.return_value.__aenter__.return_value = mock_session
        
        gen = get_db()
        session = await gen.__anext__()
        assert session == mock_session
