# database/services/interfaces/pattern_service.py

from abc import abstractmethod
from typing import List, Optional, Dict
from database.repositories.interfaces.base_service import IBaseService
from database.models.pattern import Pattern


class IPatternService(IBaseService[Pattern]):
    """Interface for pattern management."""

    @abstractmethod
    def get_by_complexity(self, skill_level: str) -> List[Pattern]:
        """Get patterns by skill level."""
        pass

    @abstractmethod
    def calculate_material_requirements(self, pattern_id: int) -> Dict[str, float]:
        """Calculate material requirements for pattern."""
        pass

    @abstractmethod
    def validate_pattern_components(self, pattern_id: int) -> List[str]:
        """Validate all components of a pattern."""
        pass

    @abstractmethod
    def duplicate_pattern(self, pattern_id: int, new_name: str) -> Optional[Pattern]:
        """Create a copy of an existing pattern."""
        pass
