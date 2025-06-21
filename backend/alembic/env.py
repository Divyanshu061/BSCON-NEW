# Path: alembic/env.py

from logging.config import fileConfig
import os
import sys
from alembic import context
from sqlalchemy import create_engine, pool

# Ensure app path is discoverable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Import settings and Base
from app.core.config import settings
from app.utils.database import Base
from app import models  # Import models to register them with Base.metadata

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name:
    fileConfig(config.config_file_name)

# Target metadata for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no DB connection)."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (with DB connection)."""
    connectable = create_engine(settings.DATABASE_URL, poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Track column type changes
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
