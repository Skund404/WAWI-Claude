# database/repositories/unit_of_work.py

from sqlalchemy.orm import Session
from .interfaces.unit_of_work import IUnitOfWork
from .implementations.pattern_repository import PatternRepository
from .implementations.leather_repository import LeatherRepository


class SQLAlchemyUnitOfWork(IUnitOfWork):
    """SQLAlchemy implementation of Unit of Work."""

    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session: Optional[Session] = None

    def __enter__(self):
        self.session = self.session_factory()
        self.patterns = PatternRepository(self.session)
        self.leather_inventory = LeatherRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()

        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


# Example usage:
"""
# Configure session factory
from sqlalchemy.orm import sessionmaker
from database.connection import engine

session_factory = sessionmaker(bind=engine)

# Create UnitOfWork instance
uow = SQLAlchemyUnitOfWork(session_factory)

# Use in service
class PatternService:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def create_pattern(self, data: dict) -> Pattern:
        with self.uow:
            pattern = Pattern(**data)
            self.uow.patterns.add(pattern)
            self.uow.commit()
            return pattern
"""