FROM python:3.14.10-slim-trixie@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b AS base
COPY --from=ghcr.io/astral-sh/uv:0.13.9@sha256:d3b601f0c7b118bc1753febf7c41cc80981df678445e0254284eecf84db79a7d /uv /uvx /bin/

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

FROM python:3.14.10-slim-trixie@sha256:22eafb370920ad8b429e0aec3fff433e0669968519f5d60469d83729c138b28b AS production

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
