import pytest
from src.auth import constants
from src.auth.models import BlacklistedToken

def test_constants():
    assert constants.JWT_TOKEN_TYPE == "bearer"
    assert constants.ERR_INVALID_CREDENTIALS == "INVALID_CREDENTIALS"

def test_blacklisted_token_str():
    token = BlacklistedToken(jti="test-jti")
    assert str(token) == "BlacklistedToken(jti=test-jti)"
