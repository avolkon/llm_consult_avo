install:
    cd project/services/auth_service && poetry install
    cd project/services/bot_service && poetry install

lint:
    cd project/services/auth_service && poetry run ruff check .
    cd project/services/bot_service && poetry run ruff check .

format:
    cd project/services/auth_service && poetry run ruff format .
    cd project/services/bot_service && poetry run ruff format .

test:
    cd project/services/auth_service && poetry run pytest
    cd project/services/bot_service && poetry run pytest

run-auth:
    cd project/services/auth_service && poetry run auth-service

run-bot:
    cd project/services/bot_service && poetry run bot-service

build-auth:
    cd project/services/auth_service && poetry build

build-bot:
    cd project/services/bot_service && poetry build

lint-auth:
    cd project/services/auth_service && poetry run ruff check .

lint-bot:
    cd project/services/bot_service && poetry run ruff check .

format-auth:
    cd project/services/auth_service && poetry run ruff format .

format-bot:
    cd project/services/bot_service && poetry run ruff format .

test-auth:
    cd project/services/auth_service && poetry run pytest

test-bot:
    cd project/services/bot_service && poetry run pytest

clean:
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    rm -rf .ruff_cache .pytest_cache .coverage htmlcov
