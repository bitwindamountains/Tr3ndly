import asyncio
from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import text
from sqlalchemy.engine import Connection

from tests.conftest import database_url
from tr3ndly.db import models  # noqa: F401 - registers tables on Base.metadata
from tr3ndly.db.base import Base
from tr3ndly.db.session import build_engine

ROOT = Path(__file__).resolve().parents[2]


def alembic_config(url: str) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.attributes["database_url"] = url
    return config


def schema_diff(connection: Connection) -> list[object]:
    context = MigrationContext.configure(connection, opts={"compare_type": True})
    return list(compare_metadata(context, Base.metadata))


async def empty_database(url: str) -> None:
    engine = build_engine(url)
    if engine.dialect.name == "postgresql":
        async with engine.begin() as connection:
            await connection.execute(text("DROP SCHEMA public CASCADE"))
            await connection.execute(text("CREATE SCHEMA public"))
    await engine.dispose()


async def diff_against_models(url: str) -> list[object]:
    engine = build_engine(url)
    async with engine.connect() as connection:
        diff = await connection.run_sync(schema_diff)
    await engine.dispose()
    return diff


def test_migrations_round_trip_without_drift(tmp_path: Path) -> None:
    url = database_url(tmp_path)
    asyncio.run(empty_database(url))
    config = alembic_config(url)

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    assert asyncio.run(diff_against_models(url)) == []
