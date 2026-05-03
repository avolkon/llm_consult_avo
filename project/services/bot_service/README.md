# bot_service

Клиент **мессенджера MAX** (long polling / webhook), Celery и вызовы LLM — в рамках системы LLM-консультаций.

## Документация MAX

- [Подготовка бота](https://dev.max.ru/docs/chatbots/bots-coding/prepare)
- Библиотека Python: [`maxapi`](https://github.com/love-apples/maxapi) (`maxapi[fastapi]` для webhook + FastAPI).

## Переменные окружения

См. `.env.example`. Минимум: `MAX_BOT_TOKEN`, `JWT_SECRET` (совпадает с auth_service).

## Команды

| Команда | Назначение |
|---------|------------|
| `poetry run bot-service` | заглушка ТЗ0 — строка в консоль |
| `poetry run max-poll` | long polling (dev; webhook в MAX должен быть отключён) |
| `poetry run max-webhook` | FastAPI + `/health` + приём webhook на `WEBHOOK_PATH` |

## Примечание

`jwt.py` и заглушки в `handlers.py` готовят проверку токена и очередь задач; полная связка с auth_service и Celery — в следующих задачах.
