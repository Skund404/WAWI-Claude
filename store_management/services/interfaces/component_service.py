from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IComponentService(Protocol):
    """Interface for component-related operations."""

    def get_by_id(self, component_id: int) -> Dict[str, Any]:
        """Get component by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all components, optionally filtered."""
        ...

    def create(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new component."""
        ...

    def update(self, component_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing component."""
        ...

    def delete(self, component_id: int) -> bool:
        """Delete a component by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for components by name or other properties."""
        ...

    def get_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Get components by type."""
        ...

    def get_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """Get materials used by a component."""
        ...

    def add_material(self, component_id: int, material_id: int, quantity: float) -> Dict[str, Any]:
        """Add a material to a component."""
        ...

    def update_material_quantity(self, component_id: int, material_id: int, quantity: float) -> Dict[str, Any]:
        """Update the quantity of a material in a component."""
        ...

    def remove_material(self, component_id: int, material_id: int) -> bool:
        """Remove a material from a component."""
        ...

    def get_patterns_using_component(self, component_id: int) -> List[Dict[str, Any]]:
        """Get patterns that use a specific component."""
        ...

    def calculate_component_cost(self, component_id: int) -> Dict[str, Any]:
        """Calculate the cost of a component based on its materials."""
        ...