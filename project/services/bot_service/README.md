# bot_service

Клиент **мессенджера MAX** (long polling / webhook), Celery и вызовы LLM — в рамках системы LLM-консультаций.

## Документация MAX

- [Подготовка бота](https://dev.max.ru/docs/chatbots/bots-coding/prepare)
- Библиотека Python: [`maxapi`](https://github.com/love-apples/maxapi) (`maxapi[fastapi]` для webhook + FastAPI).

## Переменные окружения

См. `.env.example`.

Ключевые параметры:

- `MAX_BOT_TOKEN`
- `JWT_SECRET` и `JWT_ALG` (должны совпадать с auth_service)
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `OPENROUTER_API_KEY`
- `OPENROUTER_MODEL`
- `MAX_DELIVERY_MODE` (`polling` или `webhook`)

## Команды

| Команда | Назначение |
|---------|------------|
| `poetry run bot-service` | запуск webhook сервера |
| `poetry run max-poll` | long polling (dev; webhook в MAX должен быть отключён) |
| `poetry run max-webhook` | FastAPI + `/health` + приём webhook на `WEBHOOK_PATH` |
| `poetry run celery-llm-worker` | запуск Celery worker для `llm_request` |

## Поток обработки

1. Пользователь отправляет `/token <JWT>`.
2. Bot Service валидирует JWT и сохраняет `max_auth/user_chat` в Redis.
3. Текстовый запрос отправляется в `llm_request.delay(sub, role, prompt)`.
4. Celery worker кладёт ответ в `max:outbox`.
5. `outbox_consumer` отправляет сообщение пользователю в MAX.

## Примечание

Celery worker не импортирует `maxapi` и не вызывает MAX API напрямую.
Доставка в MAX выполняется только в Bot Service через outbox consumer.
