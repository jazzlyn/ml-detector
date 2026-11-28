FROM python:3.15.2-slim-trixie@sha256:08a4c22c92b79ec821a7ad49768480039ee5b7accac3955228e75366e30abc8e AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.10@sha256:a3ea1357342c1a4bf9a0c53a3deb1b55379aefa037338d8113d5771efa01774f /uv /uvx /bin/

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
      libgl1 \
      libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./

RUN useradd -m user && \
    chown -R user:user /app

USER user

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_CACHE=1

RUN uv sync --dev --frozen --extra cpu

COPY src/ ./src/
COPY tests/ ./tests/

# run linting and code quality checks
RUN basedpyright .
RUN ruff check --no-fix .
RUN ruff format --check .

# run tests
RUN pytest -v

FROM base AS build

USER user

RUN uv sync --no-dev --frozen --extra cpu

FROM python:3.15.2-slim-trixie@sha256:08a4c22c92b79ec821a7ad49768480039ee5b7accac3955228e75366e30abc8e AS production

WORKDIR /app

RUN apt-get update && apt-get install --no-install-recommends -y \
      libgl1 \
      libglib2.0-0 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY --from=build /app/.venv ./.venv
COPY src/ ./src/

RUN useradd -m user && \
    chown -R user:user /app

USER user

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["python", "src/inference.py"]
