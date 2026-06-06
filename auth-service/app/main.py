from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import BaseHTTPException
from app.db.base import Base
from app.db.session import engine

# Важно импортировать модели, чтобы они зарегистрировались в Base.metadata.
from app.db import models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """
    Lifespan приложения.

    При старте создаём таблицы, если их ещё нет.
    Для учебного проекта это нормально.
    В production обычно используются миграции Alembic.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    """
    Создаёт и конфигурирует FastAPI-приложение.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        lifespan=lifespan,
    )

    register_routes(app)
    register_exception_handlers(app)

    return app


def register_routes(app: FastAPI) -> None:
    """
    Подключение роутеров и системных ручек.
    """

    @app.get("/health", tags=["system"])
    def health_check() -> dict[str, str]:
        settings = get_settings()

        return {
            "status": "ok",
            "service": settings.app_name,
            "env": settings.env,
        }

    app.include_router(api_router)


def register_exception_handlers(app: FastAPI) -> None:
    """
    Подключение обработчиков исключений.
    """

    @app.exception_handler(BaseHTTPException)
    async def base_http_exception_handler(
        _request: Request,
        exc: BaseHTTPException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error_code": exc.error_code,
                "message": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={
                "error_code": "internal_server_error",
                "message": "Internal server error",
            },
        )


app = create_app()
