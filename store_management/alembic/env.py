# File: alembic/env.py
# This file is responsible for configuring the Alembic environment.

import sys
import os
from pathlib import Path

# Add the project root to the Python path.
project_root = Path(__file__).resolve().parent.parent
print(f"Project root: {project_root}")
sys.path.insert(0, str(project_root))

print(f"Python executable: {sys.executable}")
print(f"sys.path: {sys.path}")

import logging
from logging.config import fileConfig

from sqlalchemy import create_engine
from sqlalchemy import pool

from alembic import context

# Import your SQLAlchemy Base and all models.
from database.sqlalchemy.models_file import Base

# Get the Alembic configuration object.
config = context.config

# Configure logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get the database URL from the configuration.
#url = config.get_main_option("sqlalchemy.url")

# Set the target metadata.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version"  # Consistent with alembic.ini
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(config.get_main_option("sqlalchemy.url"))

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version"  # Consistent with alembic.ini
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()