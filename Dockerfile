# syntax=docker/dockerfile:1
#
# Daily Signal runtime image.
#
# One image serves the API, worker, and scheduler processes; they differ only in
# the command Compose runs. Dependencies are installed in a separate layer from
# the source so edits to ``src`` do not re-download wheels, and ``uv sync
# --locked`` guarantees the image matches the committed ``uv.lock`` exactly.

FROM python:3.13-slim

# Install the pinned uv binary from its official image.
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Create the unprivileged runtime user up front so application files can be
# copied with --chown instead of a recursive chown. The venv built below is
# root-owned but world-readable, which is all the runtime user needs.
RUN useradd --create-home --uid 10001 appuser

# 1. Resolve and install third-party dependencies only. This layer is cached
#    until pyproject.toml or uv.lock changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project

# 2. Copy the application and the runtime assets it needs (README for the
#    package metadata, migrations, alembic.ini, pinned config and contracts),
#    then install the project itself.
COPY --chown=appuser:appuser README.md ./
COPY --chown=appuser:appuser src ./src
COPY --chown=appuser:appuser migrations ./migrations
COPY --chown=appuser:appuser alembic.ini ./
COPY --chown=appuser:appuser config ./config
COPY --chown=appuser:appuser contracts ./contracts
RUN uv sync --locked --no-dev

USER appuser

EXPOSE 8000

# Default process is the public API; Compose overrides this for worker and
# scheduler. The app never creates schema: migrations run as a separate step.
CMD ["uvicorn", "daily_signal.main:app", "--host", "0.0.0.0", "--port", "8000"]
