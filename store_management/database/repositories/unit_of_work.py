

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class SQLAlchemyUnitOfWork(IUnitOfWork):
    pass
"""SQLAlchemy implementation of Unit of Work."""

@inject(MaterialService)
def __init__(self, session_factory):
    pass
self.session_factory = session_factory
self.session: Optional[Session] = None

@inject(MaterialService)
def __enter__(self):
    pass
self.session = self.session_factory()
self.patterns = PatternRepository(self.session)
self.leather_inventory = LeatherRepository(self.session)
return self

@inject(MaterialService)
def __exit__(self, exc_type, exc_val, exc_tb):
    pass
if exc_type is not None:
    pass
self.rollback()
self.session.close()

@inject(MaterialService)
def commit(self):
    pass
self.session.commit()

@inject(MaterialService)
def rollback(self):
    pass
self.session.rollback()

"""
# Configure session factory
from sqlalchemy.orm import sessionmaker
from database.connection import engine

session_factory = sessionmaker(bind=engine)

# Create UnitOfWork instance
uow = SQLAlchemyUnitOfWork(session_factory)

# Use in service
class PatternService:
    pass
@inject(MaterialService)
def __init__(self, uow: IUnitOfWork):
    pass
self.uow = uow

@inject(MaterialService)
def create_pattern(self, data: dict) -> Pattern:
with self.uow:
    pass
pattern = Pattern(**data)
self.uow.patterns.add(pattern)
self.uow.commit()
return pattern
"""
