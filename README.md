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
│ │ │ ├── .env # Переменные окружения
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
│ │ ├── .env
│ │ └── Dockerfile
│ │
│ ├── docker-compose.yml
│ ├── README.md
│ └── .env.example
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

Требования
Python 3.11+

Poetry (установлен глобально)

Git

Статус
✅ Базовый скелет проекта создан
✅ Poetry настроен для обоих сервисов
✅ Makefile готов к работе
✅ Эпик 1 (Auth Service): этапы 1-5 реализованы
⏳ Разработка Bot/Celery эпиков в процессе

