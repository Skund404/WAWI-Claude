# services/interfaces/component_service.py
from typing import Dict, List, Any, Optional, Protocol


class IComponentService(Protocol):
    """Interface for the Component Service.

    The Component Service handles operations related to components used in
    leatherworking projects, including their material requirements and relationships.
    """

    def get_by_id(self, component_id: int) -> Dict[str, Any]:
        """Retrieve a component by its ID.

        Args:
            component_id: The ID of the component to retrieve

        Returns:
            A dictionary representation of the component

        Raises:
            NotFoundError: If the component with the given ID does not exist
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all components with optional filtering.

        Args:
            filters: Optional filters to apply to the component query

        Returns:
            List of dictionaries representing components
        """
        ...

    def create(self, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new component.

        Args:
            component_data: Dictionary containing component data

        Returns:
            Dictionary representation of the created component

        Raises:
            ValidationError: If the component data is invalid
        """
        ...

    def update(self, component_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing component.

        Args:
            component_id: ID of the component to update
            component_data: Dictionary containing updated component data

        Returns:
            Dictionary representation of the updated component

        Raises:
            NotFoundError: If the component with the given ID does not exist
            ValidationError: If the updated data is invalid
        """
        ...

    def delete(self, component_id: int) -> bool:
        """Delete a component by its ID.

        Args:
            component_id: ID of the component to delete

        Returns:
            True if the component was successfully deleted

        Raises:
            NotFoundError: If the component with the given ID does not exist
            ServiceError: If the component cannot be deleted (e.g., in use)
        """
        ...

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find components by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching components
        """
        ...

    def find_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Find components by type.

        Args:
            component_type: Component type to filter by

        Returns:
            List of dictionaries representing components of the specified type
        """
        ...

    def get_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """Get all materials used by a component.

        Args:
            component_id: ID of the component

        Returns:
            List of dictionaries representing materials with quantities

        Raises:
            NotFoundError: If the component with the given ID does not exist
        """
        ...

    def add_material(self,
                     component_id: int,
                     material_id: int,
                     quantity: float) -> Dict[str, Any]:
        """Add a material to a component or update its quantity.

        Args:
            component_id: ID of the component
            material_id: ID of the material to add
            quantity: Quantity of the material needed

        Returns:
            Dictionary representing the component-material relationship

        Raises:
            NotFoundError: If the component or material does not exist
            ValidationError: If the quantity is invalid
        """
        ...

    def remove_material(self, component_id: int, material_id: int) -> bool:
        """Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            True if the material was successfully removed

        Raises:
            NotFoundError: If the component or the component-material relationship does not exist
        """
        ...

    def get_components_using_material(self, material_id: int) -> List[Dict[str, Any]]:
        """Find all components that use a specific material.

        Args:
            material_id: ID of the material

        Returns:
            List of dictionaries representing components that use the material

        Raises:
            NotFoundError: If the material with the given ID does not exist
        """
        ...

    def calculate_component_cost(self, component_id: int) -> Dict[str, float]:
        """Calculate the cost of a component based on its materials.

        Args:
            component_id: ID of the component

        Returns:
            Dictionary with cost details (material_cost, labor_cost, total_cost)

        Raises:
            NotFoundError: If the component with the given ID does not exist
        """
        ...