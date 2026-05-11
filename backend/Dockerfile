FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* /code/

RUN poetry config virtualenvs.create false && poetry install --no-root --no-interaction --no-ansi

COPY . /code/

EXPOSE 8000

CMD ["sh", "-c", "poetry run alembic upgrade head && uvicorn main:app_application_instance --host 0.0.0.0 --port 8000"]

