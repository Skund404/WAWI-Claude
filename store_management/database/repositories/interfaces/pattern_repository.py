# database/repositories/interfaces/pattern_repository.py

from typing import List, Optional
from database.repositories.interfaces.base_repository import IBaseRepository
from ...models.pattern import Pattern


class IPatternRepository(IBaseRepository[Pattern]):
    """Interface for pattern repository."""

    @abstractmethod
    def get_by_skill_level(self, skill_level: str) -> List[Pattern]:
        """Get patterns by skill level."""
        pass

    @abstractmethod
    def get_with_components(self, pattern_id: int) -> Optional[Pattern]:
        """Get pattern with all its components."""
        pass

    @abstractmethod
    def search_by_criteria(self, criteria: dict) -> List[Pattern]:
        """Search patterns by given criteria."""
        pass