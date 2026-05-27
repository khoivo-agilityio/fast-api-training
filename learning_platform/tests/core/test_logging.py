import pytest
from unittest.mock import patch
from src.core.logging import configure_logging

def test_configure_logging_debug():
    with patch("logging.basicConfig") as mock_basic_config, patch("structlog.configure") as mock_structlog_config:
        configure_logging(debug=True)
        mock_basic_config.assert_called_once()
        mock_structlog_config.assert_called_once()

def test_configure_logging_info():
    with patch("logging.basicConfig") as mock_basic_config, patch("structlog.configure") as mock_structlog_config:
        configure_logging(debug=False)
        mock_basic_config.assert_called_once()
        mock_structlog_config.assert_called_once()
