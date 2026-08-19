# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:0.11.19 AS uv

FROM python:3.14-slim-bookworm

ARG APP_UID=10001
ARG APP_GID=10001

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    MCP_SERVER_NAME=local-rag \
    NOTES_DIR=/notes \
    MEMORY_DB=/data/memory.db \
    EXTENSIONS_DIR=/data/extensions \
    MODEL_PATH=/data/models/multilingual-e5-large-instruct-q8_0.gguf

COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

COPY --chown=${APP_UID}:${APP_GID} . /app

RUN groupadd --gid "${APP_GID}" app \
    && useradd --uid "${APP_UID}" --gid "${APP_GID}" --create-home app \
    && mkdir -p /data/extensions /data/models /notes \
    && chown -R app:app /data /notes

USER app

VOLUME ["/data"]

ENTRYPOINT ["python", "/app/docker/start.py"]
