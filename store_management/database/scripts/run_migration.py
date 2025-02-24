from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)


def initialize_database():
    """Initialize the database with all tables."""
engine = create_engine(DATABASE_URL)
print("Creating all tables...")
Base.metadata.create_all(engine)
print("Database initialization complete!")

if __name__ == "__main__":
    initialize_database()
