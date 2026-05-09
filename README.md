# LLM Consultation System

Система LLM-консультаций с аутентификацией и чат-ботом в мессенджере **MAX** (не Telegram).

## Структура проекта
llm_consult_avo/
├── project/
│ ├── services/
│ │ ├── auth_service/ # FastAPI сервис аутентификации
│ │ │ ├── app/
│ │ │ │ ├── main.py # FastAPI app, lifespan и /health
│ │ │ │ ├── api/ # Роутеры FastAPI
│ │ │ │ ├── core/ # Конфигурация, security, исключения
│ │ │ │ ├── db/ # SQLAlchemy модели, сессии
│ │ │ │ ├── repositories/ # Работа с БД
│ │ │ │ ├── schemas/ # Pydantic схемы
│ │ │ │ └── usecases/ # Бизнес-логика
│ │ │ ├── tests/ # Тесты
│ │ │ ├── pyproject.toml # Poetry зависимости
│ │ │ ├── .env.example # Шаблон переменных окружения
│ │ │ └── Dockerfile
│ │ │
│ │ └── bot_service/ # Бот MAX (maxapi + FastAPI webhook / polling, Celery)
│ │ ├── app/
│ │ │ ├── main.py # Точка входа
│ │ │ ├── bot/ # Хендлеры, диспетчер
│ │ │ ├── core/ # Конфигурация, JWT
│ │ │ ├── infra/ # Redis, Celery
│ │ │ ├── services/ # OpenRouter клиент
│ │ │ └── tasks/ # Celery задачи
│ │ ├── tests/
│ │ ├── pyproject.toml
│ │ ├── .env.example
│ │ └── Dockerfile
│ │
│ ├── docker-compose.yml
│ ├── README.md
│ ├── .env.auth.example
│ └── .env.bot.example
│
├── Makefile
└── .gitignore


## Команды Makefile (запуск из корня)

| Команда | Действие |
|---------|----------|
| make install | Установить зависимости для обоих сервисов |
| make run-auth | Запустить auth_service (Poetry) |
| make run-bot  | Заглушка bot_service (`bot-service`) |
| make run-max-poll | Long polling MAX (dev) |
| make run-max-webhook | FastAPI + `/health` + webhook MAX |
| make lint     | Проверить код через ruff (оба сервиса) |
| make format   | Отформатировать код через ruff (оба сервиса) |
| make test     | Запустить pytest (оба сервиса) |
| make clean    | Очистить кэш (__pycache__, .ruff_cache, и т.д.) |

### Команды для отдельных сервисов

- make lint-auth / make lint-bot
- make format-auth / make format-bot
- make test-auth / make test-bot
- make build-auth / make build-bot

## Запуск

```bash
# Установка зависимостей
make install

# Запуск сервиса аутентификации
make run-auth

# Long polling MAX (dev) или webhook: make run-max-webhook
make run-max-poll
```

Для `docker-compose` используйте отдельные файлы `project/.env.auth.example` и
`project/.env.bot.example` как шаблоны, а локальные `.env` с реальными секретами
не добавляйте в git.

Требования
Python 3.11+

Poetry (установлен глобально)

Git

Статус
✅ Базовый скелет проекта создан
✅ Poetry настроен для обоих сервисов
✅ Makefile готов к работе
✅ Эпик 1 (Auth Service): реализован
✅ Эпик 2 (Bot Core): реализован
✅ Эпик 3 (Celery/OpenRouter/Outbox Producer): реализован
✅ Эпик 4 (Response Sender): реализован
✅ Эпик 5 (документация и инфраструктура): реализован

