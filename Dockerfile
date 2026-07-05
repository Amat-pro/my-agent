FROM python:3.14-alpine AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN addgroup -S app && adduser -S -G app app

COPY pyproject.toml README.md ./
COPY app ./app

RUN python -m pip install --upgrade pip && python -m pip install .

USER app

EXPOSE 8000

CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--log-config", "app/observability/logging/uvicorn.json"]
