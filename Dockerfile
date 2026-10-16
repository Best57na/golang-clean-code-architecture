FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv

COPY pyproject.toml ./
COPY app ./app
RUN pip install .

RUN useradd --create-home appuser
USER appuser

EXPOSE 3000

# Create tables, then start the API (host/port come from PYAPP_HOST/PYAPP_PORT)
CMD ["sh", "-c", "python -m app.infrastructure.database.postgres.migration && python -m app.infrastructure.fastapi.main"]
