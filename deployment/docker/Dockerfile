FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY . .

EXPOSE 8000

# Single worker: SimulationEngine keeps tick count and its DB session in-process,
# so multiple workers would each run an independent, un-synced simulation.
#
# `alembic upgrade head` runs first so schema changes ship as reviewable, versioned
# migrations (backend/app/migrations/versions/) instead of the app mutating its own
# schema on every boot. It's a no-op once the DB is already current, so this is safe
# to run on every container start, not just the first one.
CMD python -m alembic -c backend/alembic.ini upgrade head && \
    uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 1
