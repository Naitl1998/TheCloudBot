import os
import asyncio
import logging
from functools import wraps
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator

from .models import Base

logger = logging.getLogger(__name__)

# ── Database URL ──────────────────────────────────────────────────────────────
# Priority: DATABASE_URL (PostgreSQL on Render) → SQLite fallback
# Render provides postgres:// but SQLAlchemy requires postgresql+asyncpg://
_raw_db_url = os.getenv("DATABASE_URL", "")
if _raw_db_url:
    if _raw_db_url.startswith("postgres://"):
        DATABASE_URL = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif _raw_db_url.startswith("postgresql://") and "+asyncpg" not in _raw_db_url:
        DATABASE_URL = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    else:
        DATABASE_URL = _raw_db_url
else:
    # Locally: ./zekcloud_bookings.db | Docker without PG: /data/bookings.db
    DATABASE_URL = (
        "sqlite+aiosqlite:////data/bookings.db"
        if os.environ.get("RENDER")
        else "sqlite+aiosqlite:///./zekcloud_bookings.db"
    )

_IS_SQLITE = DATABASE_URL.startswith("sqlite")

# ── Engine ──────────────────────────────────────────────────────────────────
if _IS_SQLITE:
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        connect_args={"timeout": 30},
        pool_pre_ping=True,
    )
else:
    # PostgreSQL on Render free tier — use NullPool (NO persistent connections).
    # NullPool means every DB call opens a fresh connection and closes it when done.
    # This is the ONLY reliable fix for "remaining connection slots are reserved":
    # connection pool (even pool_size=1) keeps sockets open between restarts,
    # and when Render redeploys, old + new container overlap → slots exhausted.
    # NullPool never leaks connections across restarts. Slightly slower per query
    # (~1 ms extra to establish TCP) but 100% stable on the free tier.
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool,        # no persistent connections — open/close per request
    )

# ── WAL mode + pragmas (SQLite only) ────────────────────────────────────────
# WAL (Write-Ahead Log): multiple readers + one writer simultaneously — no
# "database is locked" errors when polling + uvicorn both touch the DB at once.
if _IS_SQLITE:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, connection_record):  # type: ignore[misc]
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")    # concurrent readers
        cursor.execute("PRAGMA synchronous=NORMAL")  # safe + fast (vs FULL)
        cursor.execute("PRAGMA foreign_keys=ON")     # enforce FK constraints
        cursor.execute("PRAGMA cache_size=-32768")   # 32 MB page cache
        cursor.execute("PRAGMA busy_timeout=10000")  # 10 s retry on lock
        cursor.close()

# ── Session factory ──────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,   # explicit flush gives better control + avoids surprises
)

# Alias used by some modules (e.g. main.py server monitor)
async_session = AsyncSessionLocal


async def init_db() -> None:
    """Create all tables and apply indexes on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema ready (WAL=%s).", _IS_SQLITE)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a scoped async session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Retry utility for transient DB errors ─────────────────────────────────────
_TRANSIENT_KEYWORDS = ("connection", "closed", "timeout", "reset", "refused",
                       "ssl", "broken pipe", "server closed", "terminating")


def with_db_retry(retries: int = 3, base_delay: float = 0.5):
    """Decorator: retry an async function on transient DB errors (connection lost, etc.)."""
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, retries + 1):
                try:
                    return await fn(*args, **kwargs)
                except Exception as exc:
                    last_exc = exc
                    err = str(exc).lower()
                    if attempt < retries and any(kw in err for kw in _TRANSIENT_KEYWORDS):
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            "DB transient error in %s (attempt %d/%d): %s — retry in %.1fs",
                            fn.__name__, attempt, retries, exc, delay,
                        )
                        await asyncio.sleep(delay)
                        continue
                    raise
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator
