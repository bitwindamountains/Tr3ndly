from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine

from tr3ndly.db import models  # noqa: F401 - registers tables on Base.metadata
from tr3ndly.db.base import Base

ROOT = Path(__file__).resolve().parents[2]


def alembic_config(database_path: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "migrations"))
    config.attributes["database_url"] = f"sqlite+aiosqlite:///{database_path}"
    return config


def test_migrations_round_trip_without_drift(tmp_path: Path) -> None:
    database = tmp_path / "migrations.db"
    config = alembic_config(database)

    command.upgrade(config, "head")
    command.downgrade(config, "base")
    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database}")
    with engine.connect() as connection:
        diff = compare_metadata(
            MigrationContext.configure(connection, opts={"compare_type": True}), Base.metadata
        )
    engine.dispose()
    assert diff == []
