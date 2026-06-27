"""
Minimal production-style FastAPI app.

Demonstrates:
- Health check endpoint (used by Docker/NGINX/monitoring)
- PostgreSQL connectivity (via SQLAlchemy)
- Redis connectivity (caching example)
- Structured logging
"""

import logging
import os
import time
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
# Logs go to stdout/stderr in JSON-ish key=value format so they can be
# collected by `docker logs`, shipped to a log driver, or scraped by
# something like Loki/Promtail/ELK without extra parsing config.
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s",
)
logger = logging.getLogger("app")

# ---------------------------------------------------------------------------
# Config (from environment variables — see .env.example)
# ---------------------------------------------------------------------------
DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://app:app@db:5432/appdb"
)
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine)
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up application")
    # Create a demo table if it doesn't exist
    try:
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS visits (
                        id SERIAL PRIMARY KEY,
                        path TEXT NOT NULL,
                        created_at TIMESTAMPTZ DEFAULT now()
                    )
                    """
                )
            )
        logger.info("Database ready")
    except Exception as exc:  # noqa: BLE001
        logger.error("Database init failed: %s", exc)
    yield
    logger.info("Shutting down application")


app = FastAPI(title="DevOps Assignment API", lifespan=lifespan)


@app.middleware("http")
async def log_requests(request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start) * 1000, 2)
    logger.info(
        "method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/")
def root():
    return {"message": "DevOps assignment API is running"}


@app.get("/health")
def health():
    """
    Health check endpoint used by:
    - Docker HEALTHCHECK
    - NGINX upstream checks
    - External uptime monitors (UptimeRobot, etc.)
    Returns 200 with component status, or 503 if a dependency is down.
    """
    status = {"api": "ok", "database": "unknown", "redis": "unknown"}
    healthy = True

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        status["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        status["database"] = f"error: {exc}"
        healthy = False

    try:
        redis_client.ping()
        status["redis"] = "ok"
    except Exception as exc:  # noqa: BLE001
        status["redis"] = f"error: {exc}"
        healthy = False

    if not healthy:
        raise HTTPException(status_code=503, detail=status)
    return status


@app.get("/visits")
def record_visit():
    """
    Demo endpoint showing both Postgres (durable write) and Redis
    (fast counter / cache) being used together.
    """
    try:
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO visits (path) VALUES ('/visits')"))
            total_db = conn.execute(text("SELECT count(*) FROM visits")).scalar()
    except Exception as exc:  # noqa: BLE001
        logger.error("DB write failed: %s", exc)
        raise HTTPException(status_code=500, detail="database error") from exc

    try:
        total_cached = redis_client.incr("visits_counter")
    except Exception as exc:  # noqa: BLE001
        logger.error("Redis write failed: %s", exc)
        total_cached = None

    return {"total_visits_in_db": total_db, "total_visits_cached_in_redis": total_cached}
