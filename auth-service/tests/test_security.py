from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_returns_hash_not_plain_password() -> None:
    plain_password = "strong-password-123"

    password_hash = hash_password(plain_password)

    assert password_hash != plain_password
    assert password_hash.startswith("$2b$") or password_hash.startswith("$2a$")


def test_verify_password_success() -> None:
    plain_password = "strong-password-123"
    password_hash = hash_password(plain_password)

    assert verify_password(plain_password, password_hash) is True


def test_verify_password_wrong_password() -> None:
    plain_password = "strong-password-123"
    wrong_password = "wrong-password"
    password_hash = hash_password(plain_password)

    assert verify_password(wrong_password, password_hash) is False


def test_create_and_decode_access_token() -> None:
    token = create_access_token(
        subject=123,
        role="user",
    )

    payload = decode_token(token)

    assert payload["sub"] == "123"
    assert payload["role"] == "user"
    assert "iat" in payload
    assert "exp" in payload
    assert isinstance(payload["iat"], int)
    assert isinstance(payload["exp"], int)
    assert payload["exp"] > payload["iat"]
