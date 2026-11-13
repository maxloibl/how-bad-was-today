"""Shared pytest fixtures.

The integration fixtures are built around ``TEST_DATABASE_URL`` and never read
or destroy ``DATABASE_URL``. When ``TEST_DATABASE_URL`` is unset the integration
tests skip instead of failing.
"""

import asyncio
import os
import subprocess
import sys
from collections.abc import AsyncIterator

import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from daily_signal.infrastructure.db import models  # noqa: F401  (registers models)
from daily_signal.infrastructure.db.base import Base


def _require_test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not set; skipping integration tests")
    return url


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """The SQLAlchemy URL of the disposable test database (or skip)."""
    return _require_test_database_url()


def _asyncpg_dsn(url: str) -> str:
    """Drop the SQLAlchemy driver prefix to obtain a plain asyncpg DSN."""
    return url.replace("+asyncpg", "")


async def _reset_schema(dsn: str) -> None:
    connection = await asyncpg.connect(dsn)
    try:
        await connection.execute("DROP SCHEMA public CASCADE")
        await connection.execute("CREATE SCHEMA public")
    finally:
        await connection.close()


@pytest.fixture(scope="session")
def migrated_database(test_database_url: str) -> str:
    """Reset the schema and run ``alembic upgrade head``, returning the URL."""
    dsn = _asyncpg_dsn(test_database_url)
    asyncio.run(_reset_schema(dsn))

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        env={**os.environ, "DATABASE_URL": test_database_url},
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"alembic upgrade head failed:\n{result.stdout}\n{result.stderr}")
    return test_database_url


@pytest.fixture(scope="session")
def db_engine(migrated_database: str) -> AsyncEngine:
    """One async engine bound to the migrated test database."""
    return create_async_engine(migrated_database, poolclass=NullPool)


@pytest.fixture(scope="session")
def session_factory(db_engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Session factory wrapping the test engine."""
    return async_sessionmaker(db_engine, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def clean_tables(request: pytest.FixtureRequest) -> AsyncIterator[None]:
    """Truncate every table except ``alembic_version`` before each test.

    Only integration tests trigger this; other tests bypass the database
    entirely so the suite remains runnable without ``TEST_DATABASE_URL``.
    """
    if request.node.get_closest_marker("integration") is None:
        yield
        return

    engine = request.getfixturevalue("db_engine")
    tables = ", ".join(sorted(Base.metadata.tables))
    async with engine.begin() as connection:
        await connection.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    yield
