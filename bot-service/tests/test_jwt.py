import time

import jwt
import pytest

from app.core.config import settings
from app.core.jwt import JWTInvalidError, decode_and_validate


def make_token(
    sub: str = "42",
    role: str = "user",
    ttl_seconds: int = 3600,
) -> str:
    now = int(time.time())

    return jwt.encode(
        {
            "sub": sub,
            "role": role,
            "iat": now,
            "exp": now + ttl_seconds,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


def test_decode_and_validate_valid_token() -> None:
    token = make_token(sub="123", role="user")

    payload = decode_and_validate(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload


def test_decode_and_validate_invalid_token_raises_error() -> None:
    with pytest.raises(JWTInvalidError):
        decode_and_validate("not-a-valid-token")
