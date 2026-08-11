FROM python:3.14.7-slim-trixie@sha256:83c1cebb322d099ac9e3a3a532ba74b0146d702838b25e4c75c02fa81ffeb910 AS base
COPY --from=ghcr.io/astral-sh/uv:0.12.3@sha256:2d890623d310b57771ce840f0da5eed5fc6d657da05ffaa45d82797b53fa3abc /uv /uvx /bin/

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

FROM python:3.14.7-slim-trixie@sha256:83c1cebb322d099ac9e3a3a532ba74b0146d702838b25e4c75c02fa81ffeb910 AS production

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
