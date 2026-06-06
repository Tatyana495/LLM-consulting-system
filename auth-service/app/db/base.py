from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Единый базовый класс для всех ORM-моделей auth-service.

    Все модели SQLAlchemy должны наследоваться от этого Base.

    Пример будущего использования:

        class User(Base):
            __tablename__ = "users"
            ...

    В этом файле не должно быть конкретных моделей.
    """
