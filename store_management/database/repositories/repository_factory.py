from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/repositories/repository_factory.py

Factory for creating repository instances.
"""
logger = logging.getLogger(__name__)


class RepositoryFactory:
    pass
"""
Factory for creating repository instances.

This class provides methods for creating repositories for different models.
"""
_repository_classes: Dict[str, Type[BaseRepository]] = {'Supplier':
SupplierRepository, 'Storage': StorageRepository, 'Product':
ProductRepository}
_repositories: Dict[str, BaseRepository] = {}

@classmethod
def register_repository(cls, model_name: str, repository_class: Type[
BaseRepository]) -> None:
"""
Register a repository class for a model.

Args:
model_name: The name of the model.
repository_class: The repository class.
"""
cls._repository_classes[model_name] = repository_class
logger.debug(
f'Registered repository for {model_name}: {repository_class.__name__}'
)

@classmethod
def get_repository(cls, model_name: str, session: Session
) -> BaseRepository:
"""
Get a repository instance for a model.

Args:
model_name: The name of the model.
session: SQLAlchemy session.

Returns:
A repository instance for the model.

Raises:
ValueError: If no repository is registered for the model.
"""
key = f'{model_name}_{id(session)}'
if key in cls._repositories:
    pass
return cls._repositories[key]
if model_name not in cls._repository_classes:
    pass
raise ValueError(
f'No repository registered for model: {model_name}')
repository_class = cls._repository_classes[model_name]
repository = repository_class(session)
cls._repositories[key] = repository
return repository

@classmethod
def clear_cache(cls) -> None:
"""Clear the repository cache."""
cls._repositories.clear()
