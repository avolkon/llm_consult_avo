# auth_service

Сервис аутентификации (FastAPI) для системы LLM-консультаций.
Отвечает за регистрацию, логин и выпуск JWT-токенов.

## Запуск

```bash
poetry install
poetry run auth-service
```

Сервис поднимается на `0.0.0.0:8000`, Swagger доступен на `/docs`.
Для `ENV=local/dev/test` и `DATABASE_URL` на SQLite (`sqlite+aiosqlite://...`)
схема БД создается автоматически при старте.

## Переменные окружения

Пример в `.env.example`:

- `APP_NAME`
- `ENV`
- `JWT_SECRET`
- `JWT_ALG`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`
- `API_HOST`
- `API_PORT`

## API

- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`
- `GET /health`

### Пример register

```bash
curl -X POST http://localhost:8000/auth/register ^
  -H "Content-Type: application/json" ^
  -d "{\"email\":\"user@example.com\",\"password\":\"secret123\"}"
```

### Пример login

```bash
curl -X POST http://localhost:8000/auth/login ^
  -H "Content-Type: application/x-www-form-urlencoded" ^
  -d "username=user@example.com&password=secret123"
```

### Пример me

```bash
curl -X GET http://localhost:8000/auth/me ^
  -H "Authorization: Bearer <access_token>"
```

## Тесты

```bash
poetry run pytest -q
```

## Архитектурные границы

- auth_service не знает о MAX API, Redis и Celery.
- auth_service не хранит чатовые состояния.
- bot_service использует JWT, выпущенный этим сервисом.

