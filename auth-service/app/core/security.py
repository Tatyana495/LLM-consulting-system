from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from passlib.context import CryptContext

from app.core.config import settings


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def hash_password(password: str) -> str:
    """
    Хеширует пароль пользователя.

    На вход получает обычный пароль.
    На выход возвращает bcrypt-хеш.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Проверяет обычный пароль против сохранённого bcrypt-хеша.
    """
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str | int,
    role: str,
    expires_delta: timedelta | None = None,
) -> str:
    """
    Создаёт JWT access token.

    В payload обязательно добавляются поля:
    - sub: идентификатор пользователя;
    - role: роль пользователя;
    - iat: время выпуска токена;
    - exp: время истечения токена.
    """
    now = datetime.now(UTC)

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    expire = now + expires_delta

    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }

    return jwt.encode(
        payload=payload,
        key=settings.jwt_secret,
        algorithm=settings.jwt_alg,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Декодирует и валидирует JWT access token.

    Проверяется:
    - подпись токена;
    - алгоритм подписи;
    - срок действия exp.

    Если токен некорректный или истёк, выбрасывается ValueError.
    """
    try:
        payload = jwt.decode(
            jwt=token,
            key=settings.jwt_secret,
            algorithms=[settings.jwt_alg],
            options={
                "require": ["sub", "role", "iat", "exp"],
            },
        )
    except ExpiredSignatureError as exc:
        raise ValueError("Token has expired") from exc
    except InvalidTokenError as exc:
        raise ValueError("Invalid token") from exc

    return payload
