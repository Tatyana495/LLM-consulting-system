from typing import ClassVar

from fastapi import HTTPException, status


class BaseHTTPException(HTTPException):
    """
    Базовое HTTP-исключение для auth-service.

    Все прикладные исключения сервиса должны наследоваться от него,
    чтобы в usecase и dependencies не писать raise HTTPException вручную.
    """

    status_code: ClassVar[int] = status.HTTP_500_INTERNAL_SERVER_ERROR
    detail: ClassVar[str] = "Internal server error"
    error_code: ClassVar[str] = "internal_server_error"

    def __init__(
        self,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            status_code=self.status_code,
            detail=detail or self.detail,
            headers=headers,
        )


class UserAlreadyExistsError(BaseHTTPException):
    status_code = status.HTTP_409_CONFLICT
    detail = "User already exists"
    error_code = "user_already_exists"


class InvalidCredentialsError(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid username or password"
    error_code = "invalid_credentials"


class InvalidTokenError(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid token"
    error_code = "invalid_token"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class TokenExpiredError(BaseHTTPException):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Token has expired"
    error_code = "token_expired"

    def __init__(self, detail: str | None = None) -> None:
        super().__init__(
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class UserNotFoundError(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "User not found"
    error_code = "user_not_found"


class PermissionDeniedError(BaseHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Permission denied"
    error_code = "permission_denied"
