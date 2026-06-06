from fastapi import FastAPI

from app.core.config import settings


def create_app() -> FastAPI:
    """
    Создаёт FastAPI-приложение Bot Service.

    Здесь только:
    - создание FastAPI app;
    - подключение служебных маршрутов;
    - базовая информация о сервисе.

    Здесь не должно быть:
    - логики общения с LLM;
    - запуска aiogram polling;
    - работы с Redis или другим хранилищем токенов;
    - бизнес-логики авторизации.
    """
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
    )

    register_routes(app)

    return app


def register_routes(app: FastAPI) -> None:
    """
    Служебные маршруты Bot Service.
    """

    @app.get("/health", tags=["system"])
    async def health_check() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "env": settings.env,
        }


app = create_app()
