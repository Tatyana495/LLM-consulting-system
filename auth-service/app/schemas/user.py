from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserPublic(BaseModel):
    """
    Публичное представление пользователя.

    Используется в ответах API.
    В этой схеме намеренно нет password_hash.
    """

    id: int
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
