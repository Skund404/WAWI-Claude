from abc import ABC, abstractmethod
from typing import List, Optional, Dict

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
from models.pattern import Pattern
from core.database.base_repository import IBaseRepository

class IPatternRepository(IBaseRepository[Pattern]):
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