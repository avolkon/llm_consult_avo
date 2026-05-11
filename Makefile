install:
	cd project/services/auth_service && uv sync
	cd project/services/bot_service && uv sync

lint:
	cd project/services/auth_service && uv run ruff check .
	cd project/services/bot_service && uv run ruff check .

format:
	cd project/services/auth_service && uv run ruff format .
	cd project/services/bot_service && uv run ruff format .

test:
	cd project/services/auth_service && uv run pytest
	cd project/services/bot_service && uv run pytest

run-auth:
	cd project/services/auth_service && uv run auth-service

run-bot:
	cd project/services/bot_service && uv run bot-service

run-max-poll:
	cd project/services/bot_service && uv run max-poll

run-max-webhook:
	cd project/services/bot_service && uv run max-webhook

build-auth:
	cd project/services/auth_service && uv build

build-bot:
	cd project/services/bot_service && uv build

publish:
	cd project/services/auth_service && uv publish --dry-run
	cd project/services/bot_service && uv publish --dry-run

audit:
	cd project/services/auth_service && uv audit
	cd project/services/bot_service && uv audit

lint-auth:
	cd project/services/auth_service && uv run ruff check .

lint-bot:
	cd project/services/bot_service && uv run ruff check .

format-auth:
	cd project/services/auth_service && uv run ruff format .

format-bot:
	cd project/services/bot_service && uv run ruff format .

test-auth:
	cd project/services/auth_service && uv run pytest

test-bot:
	cd project/services/bot_service && uv run pytest

clean:
	powershell -NoProfile -Command "$$dirs = @('.ruff_cache','.pytest_cache','htmlcov'); foreach ($$d in $$dirs) { if (Test-Path $$d) { Remove-Item -Recurse -Force $$d } }; Get-ChildItem -Path . -Recurse -Directory -Filter '__pycache__' -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue; Get-ChildItem -Path . -Recurse -File -Filter '*.pyc' -Force -ErrorAction SilentlyContinue | Remove-Item -Force -ErrorAction SilentlyContinue; if (Test-Path .coverage) { Remove-Item -Force .coverage }"
