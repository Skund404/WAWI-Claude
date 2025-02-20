# database/scripts/initialize_db.py

from sqlalchemy import create_engine
from store_management.database.sqlalchemy.models import Base
from store_management.database.sqlalchemy.session import DATABASE_URL


def initialize_database():
    """Initialize the database with all tables."""
    engine = create_engine(DATABASE_URL)

    print("Creating all tables...")
    Base.metadata.create_all(engine)
    print("Database initialization complete!")


if __name__ == "__main__":
    initialize_database()