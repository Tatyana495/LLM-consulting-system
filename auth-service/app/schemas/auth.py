from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """
    Тело запроса для регистрации пользователя.

    Используется в POST /auth/register.
    """

    email: EmailStr
    password: str = Field(
        min_length=8,
        max_length=128,
        description="User password, from 8 to 128 characters",
    )


class TokenResponse(BaseModel):
    """
    Ответ с JWT access token.

    Используется после успешного логина.
    """

    access_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    """
    Ответ после успешного логина.

    Отдельный класс оставлен для читаемости API.
    Сейчас полностью совпадает с TokenResponse.
    """
