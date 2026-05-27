import pytest
from unittest.mock import patch
from src.core.client import get_s3_session, get_boto_config

def test_get_s3_session_local():
    with patch("src.config.settings.STORAGE_BACKEND", "local"):
        session = get_s3_session()
        assert session is not None

def test_get_boto_config_local():
    with patch("src.config.settings.STORAGE_BACKEND", "local"):
        config = get_boto_config()
        assert config.s3["addressing_style"] == "path"

def test_get_s3_session_aws():
    with patch("src.config.settings.STORAGE_BACKEND", "s3"):
        session = get_s3_session()
        assert session is not None

def test_get_boto_config_aws():
    with patch("src.config.settings.STORAGE_BACKEND", "s3"):
        config = get_boto_config()
        assert config.s3["addressing_style"] == "auto"
