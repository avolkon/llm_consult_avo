FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* README.md ./
RUN poetry config virtualenvs.create false
RUN poetry install --no-root --no-interaction --no-ansi

COPY app ./app
COPY .env.example ./.env.example

EXPOSE 8000

CMD ["poetry", "run", "auth-service"]
