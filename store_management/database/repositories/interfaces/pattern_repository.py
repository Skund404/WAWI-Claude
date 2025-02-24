

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class IPatternRepository(IBaseRepository[Pattern]):
    pass
"""Interface for pattern repository."""

@abstractmethod
@inject(MaterialService)
def get_by_skill_level(self, skill_level: str) -> List[Pattern]:
"""Get patterns by skill level."""
pass

@abstractmethod
@inject(MaterialService)
def get_with_components(self, pattern_id: int) -> Optional[Pattern]:
"""Get pattern with all its components."""
pass

@abstractmethod
@inject(MaterialService)
def search_by_criteria(self, criteria: dict) -> List[Pattern]:
"""Search patterns by given criteria."""
pass
