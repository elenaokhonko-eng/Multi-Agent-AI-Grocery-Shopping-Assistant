import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlmodel import SQLModel

# Add packages directory to sys.path
current_file = Path(__file__).resolve()
repo_root = current_file.parents[3]
packages_dir = repo_root / "packages"

if str(packages_dir) not in sys.path:
    sys.path.insert(0, str(packages_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))


# this is the Alembic Config object, which provides access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata


def get_url() -> str:
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        return db_url
    return config.get_main_option("sqlalchemy.url") or "sqlite:///./grocery.db"


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    db_url = get_url()
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = db_url

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
