# LLM Consultation System

Система LLM-консультаций с аутентификацией и чат-ботом в мессенджере **MAX** (не Telegram).

### Почему MAX вместо Telegram

В финальной учебной реализации выбран мессенджер **MAX** и библиотека **maxapi**: так зафиксирован стек проекта (long polling / webhook, исходящие сообщения, идентификаторы чата и пользователя). С точки зрения **архитектуры** это тот же класс задач, что и у Telegram-бота: события из мессенджера, привязка сессии к **идентификатору пользователя/чата**, очередь задач к LLM и доставка ответа обратно в диалог. Требования методички про «бота» и скриншоты переписки **корректно отражаются в MAX**; где в формулировках явно указан Telegram, однако, в связи с тем, что Telegram блокируется на территории РФ, это потребовало замены канала на MAX без изменения логики Auth Service, JWT и асинхронной цепочки Celery.

Также в отличие от исходного ТЗ изменена модель из Openrouter
в проекте применяется qwen/qwen3.5-flash-02-23
в связи с тем, что указанная в исходном ТЗ бесплатная модель недоступна

## Структура проекта

Срез репозитория (без локальных `.venv`, `__pycache__`, `.pytest_cache`, `.ruff_cache`, `auth.db`, рабочих `.env`):

```
llm_consult_avo/
├── .cursor/                   # только на машине разработчика (Cursor IDE); в git не входит
├── project/
│   ├── docker-compose.yml     # dev-брокеры + приложения; профиль prod-broker-tls — TLS redis-tls/rabbitmq-tls
│   ├── .env.auth.example
│   ├── .env.bot.example
│   ├── scripts/               # вспомогательные скрипты (в т.ч. проверка env для compose)
│   │
│   └── services/              # каталог микросервисов: auth + bot (не путать с app/services у bot)
│       │
│       ├── auth_service/      # FastAPI: регистрация, логин, JWT, /health
│       │   ├── app/
│       │   │   ├── main.py
│       │   │   ├── api/       # FastAPI-роутеры, зависимости
│       │   │   ├── core/      # config, security, rate_limiter …
│       │   │   ├── db/        # SQLAlchemy
│       │   │   ├── repositories/
│       │   │   ├── schemas/
│       │   │   └── usecases/
│       │   ├── tests/
│       │   ├── Dockerfile
│       │   ├── pyproject.toml
│       │   ├── uv.lock
│       │   ├── pytest.ini
│       │   ├── .env.example
│       │   └── README.md
│       │
│       └── bot_service/       # MAX: long polling (poll) / webhook (main); Celery+RabbitMQ; Redis; OpenRouter
│           ├── app/
│           │   ├── main.py    # FastAPI + webhook MAX
│           │   ├── poll.py    # long polling MAX
│           │   ├── bot/       # handlers, dispatcher, outbox_consumer → ответы в MAX
│           │   ├── core/
│           │   ├── infra/     # Redis; celery_app (брокер — RabbitMQ)
│           │   ├── models/
│           │   ├── services/    # auth_mapping, openrouter_client
│           │   └── tasks/       # Celery: llm_request → ответ в Redis outbox
│           ├── tests/
│           ├── Dockerfile
│           ├── pyproject.toml
│           ├── uv.lock
│           ├── pytest.ini
│           ├── .env.example
│           └── README.md
├── screenshots/               # скриншоты для отчёта: swagger, max_bot, RabbitMQ, tests
├── Разработка/                # Arch.txt, ИБ/ (в т.ч. docker-compose.dev-host-ports.yml), эпики, бэклог (DevRules — локально, см. .gitignore)
├── Makefile
├── README.md
├── LICENSE
├── ТЗ_МАКС.txt
└── .gitignore
```


## Команды Makefile (запуск из корня)

| Команда | Действие |
|---------|----------|
| make install | Установить зависимости для обоих сервисов |
| make run-auth | Запустить auth_service (uv) |
| make run-bot  | bot_service |
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

### Пошаговая проверка окружения (корень клона и Docker)

Последовательность: **шаг 1** — uv (`uv sync` в обоих сервисах); **шаг 2** — pytest; **шаг 3** — Redis и RabbitMQ в Docker; **шаг 4** — запуск `auth_service`; **шаг 5** — `GET /health`; **шаг 6** — Celery worker; **шаг 7** — `max-poll` (см. «Режимы MAX»); **шаг 8** — `POST /auth/register`; **шаг 9** — JWT в буфер (`POST /auth/login` → `access_token`); **шаг 10** — `GET /auth/me` с JWT из буфера (опционально; см. подсказку про перезапись буфера).

**До диалога с ботом в MAX:** контейнеры **шага 3** (`docker compose` с overlay портов на localhost — см. шаг 3) должны быть **запущены и оставаться работать**, иначе бот и воркер не достучатся до Redis/RabbitMQ. Без **шага 6** (`uv run celery-llm-worker`) ответ модели **не появится**: после текста пользователю может прийти только «Запрос отправлен, ответ появится в этом чате», пока очередь в RabbitMQ не обработана.

**Корень клона** — каталог `llm_consult_avo`, в нём лежат `Makefile` и папка `project/`. В блоках ниже **первая строка** переводит в каталог клона (Windows) или в ожидаемое расположение клона под `Documents/GitHub` (macOS/Linux). Если ваш клон в другом месте — замените только эту первую строку.

**Проверка, что вы в корне:** в PowerShell `(Test-Path Makefile) -and (Test-Path project)` должно быть `True`; в bash — `test -f Makefile && test -d project && echo ok`.

**Docker (Redis и RabbitMQ в шаге 3):**

- **Windows и macOS:** заранее установите и **запустите Docker Desktop** (иконка в трее/строке меню, статус *Running* / «двигатель запущен»). Без этого `docker compose` выдаст ошибку подключения к демону.
- **Linux:** должен работать демон Docker (например, `sudo systemctl start docker` для пакета `docker.io`, либо служба из вашего дистрибутива). Отдельный «Desktop» не обязателен, если `docker info` выполняется без ошибки.

#### Оглавление шагов

| Шаг | Содержание |
|-----|------------|
| [1](#step-1) | uv: `auth_service` + `bot_service` (`uv sync`) |
| [2](#step-2) | Pytest обоих сервисов |
| [3](#step-3) | Docker: Redis и RabbitMQ |
| [4](#step-4) | Запуск `auth_service` |
| [5](#step-5) | `GET /health` auth |
| [6](#step-6) | Celery worker `llm_request` |
| [7](#step-7) | `max-poll` |
| [8](#step-8) | `POST /auth/register` |
| [9](#step-9-jwt-clipboard) | JWT в буфер (`POST /auth/login`) |
| [10](#step-10) | `GET /auth/me` (проверка токена) |

Подробнее про чат в MAX: раздел [«Как найти чат с ботом в MAX»](#max-chat-howto).

#### Шпаргалка PowerShell (все шаги в одном блоке)

Подставьте **`ВАШ_ЛОГИН`** (и при необходимости путь). Docker Desktop на Windows должен быть запущен до шага 3. Шаги 4–7 и 8–10 держите в отдельных терминалах, если процесс не завершается сам.

```powershell
$R = "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"

# Шаг 1 — uv
Set-Location "$R"; Set-Location "project\services\auth_service"; uv sync; Set-Location "..\bot_service"; uv sync; Set-Location "..\..\.."

# Шаг 2 — pytest
Set-Location "$R"; Set-Location "project\services\auth_service"; uv run pytest; Set-Location "..\bot_service"; uv run pytest; Set-Location "..\..\.."

# Шаг 3 — Redis + RabbitMQ
Set-Location "$R"; Set-Location "project"; docker compose -f docker-compose.yml -f ../Разработка/ИБ/docker-compose.dev-host-ports.yml up -d redis rabbitmq; Set-Location ".."

# Шаг 4 — auth_service (терминал занят до Ctrl+C)
Set-Location "$R\project\services\auth_service"; uv run auth-service

# Шаг 5 — health (новый терминал, auth из шага 4 должен слушать :8000)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get

# Шаг 6 — Celery worker (новый терминал)
Set-Location "$R\project\services\bot_service"; uv run celery-llm-worker

# Шаг 7 — max-poll (ещё один терминал)
Set-Location "$R\project\services\bot_service"; uv run max-poll

# Шаг 8 — регистрация (email/пароль замените при необходимости)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/register" -Method Post -ContentType "application/json" -Body '{"email":"readme-demo@example.com","password":"ValidP@ss1"}'

# Шаг 9 и 10 — токен без ошибок буфера (логин + /me + по желанию буфер для MAX)
$token = (Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body "username=readme-demo@example.com&password=ValidP@ss1").access_token
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/me" -Headers @{ Authorization = "Bearer $token" }
$token | Set-Clipboard   # вставить в MAX после /token 
```

---

<a id="step-1"></a>

### Шаг 1: установка зависимостей через uv (без `make`)

Эквивалент `make install`. В конце вы снова окажетесь в корне клона.

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона (`ВАШ_ЛОГИН` и при необходимости путь).

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"
Set-Location "project\services\auth_service"; uv sync; Set-Location "..\bot_service"; uv sync; Set-Location "..\..\.."
```

**macOS (Terminal, bash/zsh)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените первую строку.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
cd project/services/auth_service && uv sync && cd ../bot_service && uv sync && cd ../../..
```

**Linux (bash)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените первую строку.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
cd project/services/auth_service && uv sync && cd ../bot_service && uv sync && cd ../../..
```

---

<a id="step-2"></a>

### Шаг 2: тесты обоих сервисов (pytest, без `make`)

Эквивалент `make test`. Ожидаемый итог: в конце двух прогонов — `passed` для всех тестов в `auth_service`, затем в `bot_service`.

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона (`ВАШ_ЛОГИН` и при необходимости путь).

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"
Set-Location "project\services\auth_service"; uv run pytest; Set-Location "..\bot_service"; uv run pytest; Set-Location "..\..\.."
```

**macOS (Terminal, bash/zsh)**

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
cd project/services/auth_service && uv run pytest && cd ../bot_service && uv run pytest && cd ../../..
```

**Linux (bash)**

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
cd project/services/auth_service && uv run pytest && cd ../bot_service && uv run pytest && cd ../../..
```

---

<a id="step-3"></a>

### Шаг 3: Redis и RabbitMQ через Docker Compose

Поднимаются только сервисы `redis` и `rabbitmq` из `project/docker-compose.yml`. Базовый файл **не публикует** порты на хост (узлы доступны только другим контейнерам в сети Compose). Для разработки на хосте с `localhost:6379` / `localhost:15672` подключайте overlay **[`Разработка/ИБ/docker-compose.dev-host-ports.yml`](Разработка/ИБ/docker-compose.dev-host-ports.yml)** (как в командах ниже).

Перед запуском: **Windows и macOS — Docker Desktop уже запущен**; **Linux — работает `docker`** (см. блок «Docker» выше).

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона.

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"
Set-Location "project"; docker compose -f docker-compose.yml -f ../Разработка/ИБ/docker-compose.dev-host-ports.yml up -d redis rabbitmq; Set-Location ".."
```

**macOS (Terminal, bash/zsh)**

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
cd project && docker compose -f docker-compose.yml -f ../Разработка/ИБ/docker-compose.dev-host-ports.yml up -d redis rabbitmq && cd ..
```

**Linux (bash)**

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
cd project && docker compose -f docker-compose.yml -f ../Разработка/ИБ/docker-compose.dev-host-ports.yml up -d redis rabbitmq && cd ..
```

Проверка (из корня клона, опционально): `docker compose -f project/docker-compose.yml -f Разработка/ИБ/docker-compose.dev-host-ports.yml ps` — у `redis` и `rabbitmq` должен быть статус `running` / `Up`. Управление RabbitMQ в браузере: [http://localhost:15672](http://localhost:15672) (логин/пароль по умолчанию у образа — часто `guest` / `guest`, если вы их не меняли в Compose; **порты на хост** подключает только overlay [`Разработка/ИБ/docker-compose.dev-host-ports.yml`](Разработка/ИБ/docker-compose.dev-host-ports.yml)).

---

<a id="step-4"></a>

### Шаг 4: запуск `auth_service` (uv)

**Перед запуском:** выполнены шаги 1–3; файл `project/services/auth_service/.env` создан и заполнен по образцу `project/services/auth_service/.env.example` (секреты не коммитьте).

Процесс занимает терминал (логи uvicorn). Остановка: `Ctrl+C`. На **Windows** брандмауэр может спросить доступ к сети для Python — для проверки на этой же машине достаточно разрешить **частную** сеть; **общедоступную** лучше не включать без необходимости.

По умолчанию HTTP-порт **8000** (см. `api_port` в настройках auth-сервиса).

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона (`ВАШ_ЛОГИН` и при необходимости путь).

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo\project\services\auth_service"
uv run auth-service
```

**macOS (Terminal, bash/zsh)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените `cd`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo/project/services/auth_service"
uv run auth-service
```

**Linux (bash)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените `cd`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo/project/services/auth_service"
uv run auth-service
```

**Swagger (`/docs`):** `http://127.0.0.1:8000/docs` — окно с этим процессом занято; откройте URL в браузере вручную или в **другом** терминале: Windows `Start-Process "http://127.0.0.1:8000/docs"`; macOS `open "http://127.0.0.1:8000/docs"`; Linux `xdg-open "http://127.0.0.1:8000/docs"`.

Эквивалент из корня репозитория через Makefile: `make run-auth` (нужен `make` и текущий каталог — корень клона).

---

<a id="step-5"></a>

### Шаг 5: проверка `GET /health` у запущенного auth-сервиса

Выполняйте в **отдельном** окне терминала, пока шаг 4 продолжает работать. Ожидаемый ответ: тело JSON с `"status": "ok"`.

Каталог в терминале для HTTP-запроса не важен; ниже в первой строке всё равно выполняется переход в корень клона — так проще держать единый стиль с шагами 1–3.

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона (`ВАШ_ЛОГИН` и при необходимости путь).

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method Get
```

**macOS (Terminal, bash/zsh)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените первую строку.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
curl -sS "http://127.0.0.1:8000/health"
```

**Linux (bash)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените первую строку.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
curl -sS "http://127.0.0.1:8000/health"
```

---

<a id="step-6"></a>

### Шаг 6: Celery worker (`llm_request`)

**Перед запуском:** выполнен шаг 3 (контейнеры Redis и RabbitMQ работают); `project/services/bot_service/.env` создан по образцу `.env.example` (минимум `REDIS_URL`, `CELERY_BROKER_URL`, `JWT_SECRET`; для реальных вызовов LLM — `OPENROUTER_API_KEY` и прочие ключи OpenRouter).

Занимает **отдельный** терминал; остановка: `Ctrl+C` (на Windows при остановке иногда печатается длинный traceback — можно закрыть вкладку терминала). В логе ожидаются строки **`Connected to amqp://...`** и **`celery@... ready.`**, в блоке `[tasks]` — задача **`llm_request`**.

На **Windows** воркер из кода запускается с пулом **`solo`** (без дочерних процессов prefork), иначе возможны ошибки доступа `WinError 5`. На macOS/Linux используется обычный пул по умолчанию.

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона.

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo\project\services\bot_service"
uv run celery-llm-worker
```

**macOS (Terminal, bash/zsh)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените `cd`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo/project/services/bot_service"
uv run celery-llm-worker
```

**Linux (bash)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените `cd`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo/project/services/bot_service"
uv run celery-llm-worker
```

---

<a id="step-7"></a>

### Шаг 7: бот MAX — long polling (`max-poll`)

**Перед запуском:** в `project/services/bot_service/.env` задан **`MAX_BOT_TOKEN`**, желательно **`MAX_DELIVERY_MODE=polling`**; **контейнеры Redis и RabbitMQ из шага 3 уже подняты** (`docker compose … up -d` и статус *Up*). **Webhook у этого бота на стороне MAX должен быть отключён**, иначе polling и webhook конфликтуют (см. ниже раздел «Режимы MAX»).

Для полной цепочки «вопрос в MAX → Celery → ответ» держите запущенными **шаг 6** (worker; **обязателен** для обработки `llm_request`) и при необходимости **шаг 4** (auth). Один процесс на терминал; остановка: `Ctrl+C` или закрытие вкладки.

В логе ожидается старт **outbox consumer** и переход диспетчера в режим ожидания обновлений MAX (**без** немедленного падения процесса).

**Windows (PowerShell)** — в первой строке укажите каталог вашего клона.

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo\project\services\bot_service"
uv run max-poll
```

**macOS (Terminal, bash/zsh)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените `cd`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo/project/services/bot_service"
uv run max-poll
```

**Linux (bash)** — если клон не в `~/Documents/GitHub/pymephi/llm_consult_avo`, замените `cd`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo/project/services/bot_service"
uv run max-poll
```

Эквивалент из корня клона: `make run-max-poll` (нужен `make`).

---

<a id="step-8"></a>

### Шаг 8: регистрация пользователя (`POST /auth/register`)

**Перед запросом:** запущен `auth_service` (шаг 4), порт **8000**. Тело запроса — JSON; минимальная длина пароля и формат email — по правилам API (см. тесты `auth_service`). Ожидается ответ **201** с полями `id`, `email`, `role`, `created_at`. Если email уже занят — **409**, используйте другой `email` в теле.

**Windows (PowerShell)** — подставьте каталог клона и при необходимости email/пароль в теле JSON.

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/register" -Method Post -ContentType "application/json" -Body '{"email":"readme-demo@example.com","password":"ValidP@ss1"}'
```

**macOS (Terminal, bash/zsh)**

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
curl -sS -w "\nHTTP_CODE:%{http_code}\n" -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"readme-demo@example.com","password":"ValidP@ss1"}'
```

**Linux (bash)**

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
curl -sS -w "\nHTTP_CODE:%{http_code}\n" -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"readme-demo@example.com","password":"ValidP@ss1"}'
```

---

<a id="step-9-jwt-clipboard"></a>

### Шаг 9: JWT в буфер обмена (`POST /auth/login` → `access_token`)

**Перед запросом:** `auth_service` на **8000**; пользователь с таким `username` (email) и паролем уже создан (**шаг 8** или ранее). Подставьте в команды **те же** `username` и `password`, что при регистрации.

В буфер попадает **только** строка **JWT** из поля `access_token`. Дальше в MAX: команда вида `/token <вставить из буфера>`.

**Windows (PowerShell)**

```powershell
Set-Location "C:\Users\ВАШ_ЛОГИН\Documents\GitHub\pymephi\llm_consult_avo"
(Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body "username=readme-demo@example.com&password=ValidP@ss1").access_token | Set-Clipboard
```

**macOS (Terminal, bash/zsh)** — нужен `python3` (обычно уже есть). Буфер: `pbcopy`.

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
curl -sS -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=readme-demo@example.com&password=ValidP@ss1" \
| python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'], end='')" \
| pbcopy
```

**Linux (bash)** — нужны `curl` и `python3`; в буфер X11: `xclip` (пакет `xclip`). На Wayland без XWayland последнюю часть замените на `| wl-copy` (пакет `wl-clipboard`).

```bash
cd "$HOME/Documents/GitHub/pymephi/llm_consult_avo"
curl -sS -X POST "http://127.0.0.1:8000/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=readme-demo@example.com&password=ValidP@ss1" \
| python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'], end='')" \
| xclip -selection clipboard
```

---

<a id="step-10"></a>

### Шаг 10: проверка JWT через `GET /auth/me` (буфер обмена)

**Перед запросом:** `auth_service` на **8000**; в буфере **ровно** та же строка JWT, что выдавал **шаг 9** (без пробелов и постороннего текста). Удобнее выполнять **сразу после шага 9**, **до** копирования чего-либо ещё: после вставки токена в MAX или других действий буфер может уже не содержать JWT — тогда `/auth/me` вернёт «Недействительный токен», хотя ранее выданный токен для бота ещё может быть действителен. В таком случае повторите **шаг 9** и эту команду подряд **или** считайте интеграцию проверенной по ответам бота в MAX.

**Windows (PowerShell)** — надёжный вариант **без буфера**: сначала логин в переменную, потом запрос (подставьте свой email/пароль).

```powershell
$token = (Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/login" -Method Post -ContentType "application/x-www-form-urlencoded" -Body "username=readme-demo@example.com&password=ValidP@ss1").access_token
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/me" -Headers @{ Authorization = "Bearer $token" }
```

Токен в буфер для MAX (после первой строки с `$token` можно отдельно выполнить):

```powershell
$token | Set-Clipboard
```

Вариант **только из буфера** (после шага 9), если в буфере ровно одна строка JWT — в **PowerShell 5.1** без `-Format`:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/auth/me" -Headers @{ Authorization = "Bearer $((Get-Clipboard).Trim())" }
```

Если с буфером снова «Недействительный токен», используйте блок с **`$token`** выше: clipboard в Windows часто не совпадает с тем, что вы ожидаете.

В PowerShell **7+** при чтении буфера по желанию: `(Get-Clipboard -Format Text).Trim()`.

**macOS (Terminal, bash/zsh)**

```bash
curl -sS "http://127.0.0.1:8000/auth/me" -H "Authorization: Bearer $(pbpaste | tr -d '\n\r')"
```

**Linux (bash)** — буфер X11 из `xclip`; на Wayland замените `$(xclip -selection clipboard -o)` на `$(wl-paste -n)`.

```bash
curl -sS "http://127.0.0.1:8000/auth/me" -H "Authorization: Bearer $(xclip -selection clipboard -o | tr -d '\n\r')"
```

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
`project/.env.bot.example` только как шаблоны. `docker-compose` читает рабочие
env-файлы сервисов: `project/services/auth_service/.env` и
`project/services/bot_service/.env`.
Локальные env-файлы с реальными секретами не добавляйте в git.

## Production и безопасность (ИБ)

- **Redis и RabbitMQ (bot):** в `ENV=prod|production` в коде требуются **`REDIS_URL`** с **`rediss://`** и **`CELERY_BROKER_URL`** с **`amqps://`**; запрещены `guest:guest` и явное ослабление проверки TLS в URL. Узел **только во внутренней сети**, без публикации портов в интернет. Эталон TLS-брокеров в репозитории: сервисы **`redis-tls`** и **`rabbitmq-tls`** в [`project/docker-compose.yml`](project/docker-compose.yml) (профиль **`prod-broker-tls`**): `docker compose --profile prod-broker-tls up -d redis-tls rabbitmq-tls` из каталога `project/` после `make tls-certs` или `python project/scripts/gen_sample_tls_certs.py` (из корня клона). Задайте **`REDIS_PASSWORD`** и **`RABBITMQ_PASSWORD`** в окружении (в бою — сильные секреты; в файле есть только подстановки для парсинга compose при обычном dev без этих переменных). В `.env` бота для этого примера хосты **`redis-tls`** и **`rabbitmq-tls`** (порт AMQP TLS **5671**).
- **Redis: целостность данных** (опционально, рекомендуется в prod): `REDIS_INTEGRITY_SECRET` в `bot_service` — одинаковая строка в процессе webhook и в **Celery worker** (подпись `max_auth:*` и `max:outbox`). Без секрета поведение как раньше (обратная совместимость). Секрет есть у приложения: это не замена сетевой изоляции Redis.
- **Секреты** в бою — Vault, Kubernetes Secrets или аналог облака; не класть в git.
- **Лимит размера HTTP-тела** дублируйте на reverse proxy, например nginx: `client_max_body_size 1m;` в `server` / `location`.
- **Trust proxy**: в `auth_service` переменная `TRUSTED_PROXY_HEADERS=true` только если `X-Forwarded-For` выставляет **ваш** nginx/traefik; иначе возможен обход rate limit.
- **Rate limit (auth)**: лимиты slowapi считаются **в памяти процесса**; несколько реплик без общего backend умножают лимиты; при жёстких требованиях — Redis для slowapi или WAF на edge.
- **JWT_AUDIENCE** (опционально): одинаковое значение в auth и bot — claim `aud` и строгая проверка.
- **OpenRouter** при `ENV=prod` в bot: только `https` и хост `openrouter.ai`.
- **Логи промптов**: при `ENV=prod|production` по умолчанию фрагменты промптов **не** логируются (`LOG_PROMPT_CONTENT` можно не задавать); `LOG_PROMPT_CONTENT=true` включает логи и в prod.
- **MAX_BOT_TOKEN**: в prod плейсхолдер или пустое значение блокирует старт — см. валидацию в `bot_service`.
- **Swagger** `/docs`: отключён при `ENV=prod` или `production` в обоих сервисах.
- **Webhook MAX** (опционально): модель доверия MAX/maxapi, переменные `WEBHOOK_REQUEST_SECRET`, `WEBHOOK_REQUEST_HEADER`, `WEBHOOK_ALLOWED_CIDRS`, `WEBHOOK_FORWARDED_FOR_TRUST_HOPS` и пример nginx — [`Разработка/ИБ/ИБ_webhook_MAX_доверие.txt`](Разработка/ИБ/ИБ_webhook_MAX_доверие.txt).
- **Регистрация / email**: политика ответа 409 — [`Разработка/ИБ/ИБ_политика_email_при_регистрации.txt`](Разработка/ИБ/ИБ_политика_email_при_регистрации.txt).
- **Защита от prompt injection** в боте: длина промпта + regex-блокировки; модель LLM остаётся отдельной поверхностью — не считать защиту полной.
- **Celery (bot)**: смена `CELERY_BROKER_URL` требует **перезапуска** воркера (значение подхватывается при старте процесса).
- **JWT (auth)**: реализовано через **PyJWT**; периодически запускайте `make audit` / `uv audit` в CI и локально.

### Аудит зависимостей (CVE)

```bash
make audit
```

или в каждом сервисе: `uv audit`. Регулярный аудит (например, в pipeline при изменении lock-файлов) снижает репутационный и CVE-риск за счёт своевременных обновлений.

### Чек-лист и отчёты ИБ

Папка [`Разработка/ИБ/`](Разработка/ИБ/): чек-лист, аудиты, отчёт о выполнении задания; опциональный overlay Docker Compose для портов брокеров на localhost — [`docker-compose.dev-host-ports.yml`](Разработка/ИБ/docker-compose.dev-host-ports.yml).

## Пользовательский flow проверки

Типовой сценарий для проверки системы:

1. Пользователь регистрируется в `auth_service` через `POST /auth/register`.
2. Пользователь выполняет логин через `POST /auth/login` и получает JWT.
3. Пользователь отправляет JWT боту в MAX командой `/token <JWT>`.
4. Bot Service валидирует JWT и сохраняет производное auth-состояние в Redis:
   `max_auth:<max_user_id>` и `user_chat:<sub>`.
5. Пользователь отправляет обычный текстовый вопрос в MAX.
6. Bot Service отправляет задачу `llm_request(sub, role, prompt)` в Celery/RabbitMQ.
7. Celery worker вызывает OpenRouter и кладёт ответ в Redis LIST `max:outbox`.
8. Outbox consumer внутри Bot Service читает `max:outbox` через `BLPOP` и отправляет ответ пользователю в MAX.

В текущей учебной версии пользователь вручную передаёт JWT через `/token`.
User-friendly авторизация без ручного JWT вынесена в backlog как первая задача после экзамена.

<a id="max-chat-howto"></a>

### Как найти чат с ботом в MAX и какие команды отправлять

Бот в мессенджере: **`@id312604366253_bot`**. Страница для открытия в браузере или в приложении: [max.ru/id312604366253_bot](https://max.ru/id312604366253_bot).

**Где в README команды шага 9 (JWT в буфер):** подзаголовок **[Шаг 9: JWT в буфер обмена](#step-9-jwt-clipboard)** — в разделе **«Пошаговая проверка окружения»** ближе к началу файла (три блока: Windows / macOS / Linux). По порядку в документе: **после шага 8**, **перед шагом 10**, ещё **до** раздела «Запуск».

**Перед открытием чата:** убедитесь, что **Docker** уже поднял **Redis и RabbitMQ** (**шаг 3**) — без них и без работающего **Celery worker** (**шаг 6**) ответ LLM в MAX не придёт. Желательно уже иметь **JWT в буфере обмена**: выполните **шаг 8** (регистрация, если пользователя ещё нет) и **шаг 9** (готовые команды — по ссылке выше). Минимум для ответов бота: контейнеры **шага 3**, **auth_service** (**шаг 4**, порт 8000), **celery-llm-worker** (**шаг 6**), **max-poll** (**шаг 7**).

**Как открыть диалог**

1. Установите приложение **MAX** (если ещё нет) и войдите в аккаунт.
2. Перейте по ссылке [max.ru/id312604366253_bot](https://max.ru/id312604366253_bot) и нажмите открытие в приложении **или** в поиске по чатам/ботам введите **`@id312604366253_bot`** и откройте найденного бота.
3. Откройте чат с ботом.

**Порядок команд в чате**

1. Первое сообщение: **`/start`** — инициализация диалога с ботом.
2. Затем отправьте **`/token `** и сразу после пробела **вставьте JWT из буфера** (в Windows обычно **Ctrl+V** в поле ввода). Итоговое сообщение: `/token <ваш_токен_одной_строкой>`.
3. После успешной привязки токена можно писать **обычный текст** — вопрос для LLM (цепочка Celery → OpenRouter → ответ в MAX описана в списке сценария выше).

Если бот не реагирует или приходит только «Запрос отправлен…» без ответа модели, проверьте: **Redis и RabbitMQ** в Docker (шаг 3, `docker compose -f project/docker-compose.yml -f Разработка/ИБ/docker-compose.dev-host-ports.yml ps`), **Celery worker** (шаг 6), **polling** локально (шаг 7), webhook у бота на стороне MAX **отключён** («Режимы MAX» ниже), токен не просрочен (повторите **шаг 9** при необходимости).

## Режимы MAX

Bot Service поддерживает два режима получения событий MAX:

- `polling` — удобен для локальной разработки, запускается через `make run-max-poll`.
- `webhook` — используется для Docker/production-сценария, запускается через `make run-max-webhook` или `project/docker-compose.yml`.

Polling и webhook нельзя использовать одновременно для одного MAX-бота.
Перед запуском polling webhook должен быть отключён на стороне MAX, а для webhook нужен публичный HTTPS URL, зарегистрированный в настройках бота.

Требования
Python 3.11+

**uv** ([установка](https://docs.astral.sh/uv/getting-started/installation/); доступен в `PATH`)

Git

Статус
✅ Базовый скелет проекта создан
✅ uv настроен для обоих сервисов (`pyproject.toml`, `uv.lock`)
✅ Makefile готов к работе
✅ Эпик 1 (Auth Service): реализован
✅ Эпик 2 (Bot Core): реализован
✅ Эпик 3 (Celery/OpenRouter/Outbox Producer): реализован
✅ Эпик 4 (Response Sender): реализован
✅ Эпик 5 (документация и инфраструктура): реализован

