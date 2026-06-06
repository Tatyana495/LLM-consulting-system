from typing import Any

import jwt
from jwt import ExpiredSignatureError
from jwt import InvalidTokenError as PyJWTInvalidTokenError

from app.core.config import settings


class JWTValidationError(ValueError):
    """
    Базовая ошибка проверки JWT в Bot Service.
    """


class JWTExpiredError(JWTValidationError):
    """
    Срок действия JWT истёк.
    """


class JWTInvalidError(JWTValidationError):
    """
    JWT некорректен: неверная подпись, алгоритм, payload
    или отсутствуют обязательные поля.
    """


def decode_and_validate(token: str) -> dict[str, Any]:
    """
    Декодирует и валидирует JWT.

    Bot Service не создаёт токены.
    Он только проверяет токены, выпущенные Auth Service.

    Проверяется:
    - подпись токена;
    - алгоритм подписи;
    - срок действия exp;
    - наличие обязательных полей sub, role, iat, exp.

    Возвращает payload токена.

    При ошибке выбрасывает:
    - JWTExpiredError, если токен истёк;
    - JWTInvalidError, если токен некорректен.
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
        raise JWTExpiredError("Token has expired") from exc
    except PyJWTInvalidTokenError as exc:
        raise JWTInvalidError("Invalid token") from exc

    subject = payload.get("sub")
    role = payload.get("role")

    if not subject:
        raise JWTInvalidError("Token payload does not contain sub")

    if not role:
        raise JWTInvalidError("Token payload does not contain role")

    return payload
