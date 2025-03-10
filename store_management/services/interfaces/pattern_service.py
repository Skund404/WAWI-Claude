from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IPatternService(Protocol):
    """Interface for pattern-related operations."""

    def get_by_id(self, pattern_id: int) -> Dict[str, Any]:
        """Get pattern by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all patterns, optionally filtered."""
        ...

    def create(self, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new pattern."""
        ...

    def update(self, pattern_id: int, pattern_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing pattern."""
        ...

    def delete(self, pattern_id: int) -> bool:
        """Delete a pattern by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for patterns by name or other properties."""
        ...

    def get_by_skill_level(self, skill_level: str) -> List[Dict[str, Any]]:
        """Get patterns by skill level."""
        ...

    def get_pattern_components(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get all components for a pattern."""
        ...

    def add_component_to_pattern(self, pattern_id: int, component_id: int) -> Dict[str, Any]:
        """Add a component to a pattern."""
        ...

    def remove_component_from_pattern(self, pattern_id: int, component_id: int) -> bool:
        """Remove a component from a pattern."""
        ...

    def get_patterns_by_project_type(self, project_type: str) -> List[Dict[str, Any]]:
        """Get patterns by project type."""
        ...

    def get_material_requirements(self, pattern_id: int) -> Dict[str, Any]:
        """Get material requirements for a pattern."""
        ...

    def get_products_using_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Get products that use a specific pattern."""
        ...