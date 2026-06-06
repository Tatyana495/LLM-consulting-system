# LLM Consulting System

Двухсервисная система LLM-консультаций с авторизацией через JWT, Telegram-ботом, асинхронной обработкой запросов через RabbitMQ/Celery и использованием Redis.

## Описание проекта

Проект реализует распределённую систему из двух независимых сервисов:

- **Auth Service** — сервис регистрации, логина и выпуска JWT-токенов.
- **Bot Service** — Telegram-бот, который принимает JWT, валидирует его и отправляет LLM-запросы в очередь.

Главная идея проекта — разделение ответственности.

Auth Service работает с пользователями, паролями и JWT.

Bot Service не хранит пользователей, не регистрирует их, не выполняет логин и не обращается напрямую к базе данных Auth Service. Он доверяет только корректно подписанному и не истёкшему JWT-токену.

LLM-запросы не выполняются прямо в Telegram-хэндлерах. Вместо этого бот публикует задачу в RabbitMQ, Celery worker забирает её из очереди, обращается к OpenRouter и отправляет ответ пользователю в Telegram.

## Архитектура

```text
Пользователь
    |
    v
Telegram Bot / aiogram
    |
    | /token <jwt>
    v
Redis
хранит JWT, привязанный к Telegram user_id
    |
    | обычный текстовый запрос
    v
RabbitMQ
очередь Celery-задач
    |
    v
Celery Worker
    |
    v
OpenRouter API
    |
    v
Telegram API
ответ пользователю
```

## Роли компонентов

| Компонент | Назначение |
|---|---|
| Auth Service | Регистрация пользователей, логин, выпуск JWT |
| Bot Service | Telegram-бот, проверка JWT, постановка LLM-задач в очередь |
| RabbitMQ | Брокер задач Celery |
| Redis | Хранение JWT по Telegram user_id и backend результатов Celery |
| Celery Worker | Асинхронная обработка LLM-запросов |
| OpenRouter | Внешний LLM API |
| SQLite | База данных Auth Service |

## Структура проекта

```text
llm-consulting-system
├── auth-service
│   ├── app
│   │   ├── api
│   │   ├── core
│   │   ├── db
│   │   ├── repositories
│   │   ├── schemas
│   │   └── usecases
│   ├── tests
│   ├── .env.example
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── uv.lock
│
├── bot-service
│   ├── app
│   │   ├── bot
│   │   ├── core
│   │   ├── infra
│   │   ├── services
│   │   └── tasks
│   ├── tests
│   ├── .env.example
│   ├── pyproject.toml
│   ├── pytest.ini
│   └── uv.lock
│
├── image
│   ├── 01-docker-infra-running.png
│   ├── 02-auth-service-started.png
│   ├── 03-auth-register-swagger.png
│   ├── 04-auth-login-swagger.png
│   ├── 05-auth-me-swagger.png
│   ├── 06-celery-worker-running.png
│   ├── 07-bot-runner-polling.png
│   ├── 08-telegram-bot-flow.png
│   ├── 09-rabbitmq-overview.png
│   └── 10-rabbitmq-celery-queue.png
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

## Auth Service

Auth Service реализован на FastAPI.

Он отвечает только за пользователей и JWT:

- регистрация пользователя;
- хеширование пароля;
- логин пользователя;
- выпуск JWT;
- проверка текущего пользователя через `/auth/me`.

### Endpoint-ы

| Метод | Endpoint | Описание |
|---|---|---|
| POST | `/auth/register` | Регистрация пользователя |
| POST | `/auth/login` | Логин и получение JWT |
| GET | `/auth/me` | Получение текущего пользователя по JWT |
| GET | `/health` | Проверка состояния сервиса |

JWT содержит поля:

```text
sub
role
iat
exp
```

## Bot Service

Bot Service реализован на aiogram и FastAPI.

Он не создаёт JWT и не работает с базой данных Auth Service. Его задача — принять токен, проверить его и разрешить пользователю отправлять LLM-запросы.

### Команды Telegram-бота

| Команда | Описание |
|---|---|
| `/start` | Показывает инструкцию |
| `/token <jwt>` | Сохраняет JWT пользователя в Redis |
| `/logout` | Удаляет JWT пользователя из Redis |
| обычный текст | Отправляет LLM-запрос в очередь, если JWT валиден |

JWT сохраняется в Redis по ключу:

```text
token:<telegram_user_id>
```

## Переменные окружения

В репозитории хранятся только `.env.example`.

Реальные `.env` файлы не коммитятся.

### Auth Service

Создать `.env`:

```powershell
cd auth-service
Copy-Item .env.example .env
```

Пример:

```env
APP_NAME=auth-service
ENV=local

JWT_SECRET=change-me-auth-secret
JWT_ALG=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

SQLITE_PATH=./auth.db
```

### Bot Service

Создать `.env`:

```powershell
cd bot-service
Copy-Item .env.example .env
```

Для локального запуска на Windows, когда Redis и RabbitMQ запущены в Docker, а Bot Service запускается через `uv run`, нужно использовать `localhost`:

```env
APP_NAME=bot-service
ENV=local

BOT_TOKEN=your-real-telegram-bot-token

AUTH_SERVICE_URL=http://localhost:8000

JWT_SECRET=change-me-auth-secret
JWT_ALG=HS256

RABBITMQ_URL=amqp://guest:guest@localhost:5672/
REDIS_URL=redis://localhost:6379/0

OPENROUTER_API_KEY=your-real-openrouter-api-key
OPENROUTER_MODEL=openai/gpt-4o-mini
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Важно: `JWT_SECRET` и `JWT_ALG` должны совпадать в Auth Service и Bot Service.

## Запуск инфраструктуры

Redis и RabbitMQ запускаются через Docker Compose.

Из корня проекта:

```powershell
docker compose up -d
```

Проверка:

```powershell
docker ps
```

Должны быть запущены контейнеры:

```text
llm-redis
llm-rabbitmq
```

RabbitMQ Management UI доступен по адресу:

```text
http://localhost:15672
```

Логин и пароль:

```text
guest / guest
```

## Запуск Auth Service

В отдельном терминале:

```powershell
cd auth-service
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

Health endpoint:

```text
http://127.0.0.1:8000/health
```

## Запуск Bot Service

### Celery worker

В отдельном терминале:

```powershell
cd bot-service
uv sync
uv run celery -A app.infra.celery_app.celery_app worker --loglevel=info --pool=solo
```

Для Windows используется параметр:

```text
--pool=solo
```

В логах worker должна быть задача:

```text
[tasks]
  . llm_request
```

Также должно быть видно подключение к RabbitMQ:

```text
Connected to amqp://guest:**@127.0.0.1:5672//
```

### Telegram bot runner

В отдельном терминале:

```powershell
cd bot-service
uv run python -m app.bot_runner
```

В логах должно быть:

```text
Start polling
Run polling for bot @llm_consult_bot
```

## Пользовательский сценарий

1. Открыть Swagger Auth Service:

```text
http://127.0.0.1:8000/docs
```

2. Зарегистрировать пользователя через `POST /auth/register`.

Пример email для демонстрации:

```text
surname@email.com
```

3. Выполнить логин через `POST /auth/login`.

Так как используется `OAuth2PasswordRequestForm`, email вводится в поле `username`.

4. Скопировать `access_token`.

5. В Telegram отправить боту:

```text
/token <access_token>
```

6. После успешной авторизации отправить обычный вопрос:

```text
Что такое RabbitMQ простыми словами?
```

7. Бот сразу отвечает:

```text
Запрос принят. Я отправил его в очередь обработки.
```

8. Celery worker обрабатывает задачу и отправляет пользователю ответ от LLM.

## Тестирование

В проекте есть unit, integration и mock-тесты.

### Auth Service

Проверяется:

- хеширование пароля;
- проверка правильного и неправильного пароля;
- создание и декодирование JWT;
- регистрация пользователя через HTTP;
- логин через HTTP;
- `/auth/me` с Bearer token;
- негативные сценарии: повторная регистрация, неверный пароль, отсутствие токена, неверный токен.

Запуск:

```powershell
cd auth-service
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Ожидаемый результат:

```text
All checks passed
25 files already formatted
9 passed
```

### Bot Service

Проверяется:

- валидный JWT успешно декодируется;
- некорректный JWT отклоняется;
- `/token <jwt>` сохраняет токен в fake Redis;
- без токена Celery не вызывается;
- с валидным токеном вызывается `llm_request.delay(...)`;
- OpenRouter-клиент тестируется через `respx` без реального интернет-запроса.

Запуск:

```powershell
cd bot-service
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Ожидаемый результат:

```text
All checks passed
22 files already formatted
6 passed
```

## Подтверждение асинхронной архитектуры

RabbitMQ реально используется как брокер Celery. Bot Service не вызывает OpenRouter напрямую из Telegram-хэндлера. Вместо этого хэндлер публикует задачу:

```python
llm_request.delay(
    tg_chat_id=message.chat.id,
    prompt=message.text,
)
```

Celery worker получает задачу из RabbitMQ, вызывает OpenRouter и отправляет результат пользователю в Telegram.

Redis реально используется для хранения JWT, привязанного к Telegram user_id:

```text
token:<telegram_user_id> -> JWT
```

## Скриншоты

Скриншоты подтверждения работы находятся в папке `image/`.

| Файл | Что подтверждает |
|---|---|
| `01-docker-infra-running.png` | Redis и RabbitMQ запущены через Docker Compose |
| `02-auth-service-started.png` | Auth Service запущен через Uvicorn |
| `03-auth-register-swagger.png` | Регистрация пользователя через Swagger |
| `04-auth-login-swagger.png` | Логин и получение JWT |
| `05-auth-me-swagger.png` | `/auth/me` работает по Bearer token |
| `06-celery-worker-running.png` | Celery worker подключён к RabbitMQ и видит задачу `llm_request` |
| `07-bot-runner-polling.png` | Telegram bot runner запущен |
| `08-telegram-bot-flow.png` | Работа Telegram-бота: `/start`, `/token`, LLM-запрос и ответ |
| `09-rabbitmq-overview.png` | RabbitMQ Overview: активные connections, channels, queues, consumers |
| `10-rabbitmq-celery-queue.png` | Очередь `celery` с активным consumer |

## Почему реализация корректна

Реализация соответствует требованиям:

- Auth Service и Bot Service разделены логически и технически.
- Auth Service отвечает только за регистрацию, логин и выпуск JWT.
- Bot Service не хранит пользователей и не обращается к БД Auth Service.
- JWT создаётся только в Auth Service.
- Bot Service только валидирует JWT.
- Без токена бот отказывает в доступе.
- JWT сохраняется в Redis по Telegram user_id.
- LLM-запросы не выполняются в Telegram-хэндлере.
- Bot Service публикует задачи в RabbitMQ.
- Celery worker обрабатывает задачи асинхронно.
- Redis и RabbitMQ реально участвуют в логике приложения.
- Unit, integration и mock-тесты проходят локально.
- Внешние сервисы в тестах не вызываются напрямую.

## Очистка перед публикацией

Перед публикацией в репозиторий не должны попадать:

```text
.env
.venv
auth.db
__pycache__
.pytest_cache
.ruff_cache
```

Эти файлы и папки исключены через `.gitignore`.

Проверка структуры:

```powershell
tree /F
```
