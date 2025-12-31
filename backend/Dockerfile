ARG PYTHON_VERSION=3.13.10
FROM python:${PYTHON_VERSION}-slim AS base

ARG POETRY_VERSION=2.1.1
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_VERSION=${POETRY_VERSION} \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

FROM base AS build

ENV PATH="$POETRY_HOME/bin:$PATH"

RUN apt update \
  && apt install -y --no-install-recommends \
  build-essential \
  curl \
  pkg-config \
  && curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

COPY poetry.lock pyproject.toml ./
RUN poetry install --only main --no-root

COPY . ./
RUN poetry install --only main

FROM base AS runtime

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=build /app ./
