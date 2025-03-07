# services/interfaces/component_service.py
"""
Interface for Component Service that manages component-related business logic.
"""

from abc import ABC, abstractmethod
from database.models.components import Component
from database.models.enums import ComponentType
from datetime import datetime
from typing import Any, Dict, List, Optional


class IComponentService(ABC):
    """Interface for the Component Service that handles operations related to components."""

    @abstractmethod
    def get_component(self, component_id: int) -> Component:
        """
        Retrieve a component by its ID.

        Args:
            component_id: ID of the component to retrieve

        Returns:
            Component: The retrieved component

        Raises:
            NotFoundError: If the component does not exist
        """
        pass

    @abstractmethod
    def get_components(self, **filters) -> List[Component]:
        """
        Retrieve components based on optional filters.

        Args:
            **filters: Optional keyword arguments for filtering components

        Returns:
            List[Component]: List of components matching the filters
        """
        pass

    @abstractmethod
    def create_component(self, component_data: Dict[str, Any]) -> Component:
        """
        Create a new component with the provided data.

        Args:
            component_data: Data for creating the component

        Returns:
            Component: The created component

        Raises:
            ValidationError: If the component data is invalid
        """
        pass

    @abstractmethod
    def update_component(self, component_id: int, component_data: Dict[str, Any]) -> Component:
        """
        Update a component with the provided data.

        Args:
            component_id: ID of the component to update
            component_data: Data for updating the component

        Returns:
            Component: The updated component

        Raises:
            NotFoundError: If the component does not exist
            ValidationError: If the component data is invalid
        """
        pass

    @abstractmethod
    def delete_component(self, component_id: int) -> bool:
        """
        Delete a component by its ID.

        Args:
            component_id: ID of the component to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the component does not exist
        """
        pass

    @abstractmethod
    def get_components_by_type(self, component_type: ComponentType) -> List[Component]:
        """
        Retrieve components filtered by their type.

        Args:
            component_type: Type of components to retrieve

        Returns:
            List[Component]: List of components of the specified type
        """
        pass

    @abstractmethod
    def get_component_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve materials associated with a component.

        Args:
            component_id: ID of the component

        Returns:
            List[Dict[str, Any]]: List of materials with quantities used in the component

        Raises:
            NotFoundError: If the component does not exist
        """
        pass

    @abstractmethod
    def add_material_to_component(
        self, component_id: int, material_id: int, quantity: float
    ) -> bool:
        """
        Add a material to a component or update its quantity.

        Args:
            component_id: ID of the component
            material_id: ID of the material to add
            quantity: Quantity of the material to use

        Returns:
            bool: True if the material was added/updated successfully

        Raises:
            NotFoundError: If the component or material does not exist
            ValidationError: If the quantity is invalid
        """
        pass

    @abstractmethod
    def remove_material_from_component(self, component_id: int, material_id: int) -> bool:
        """
        Remove a material from a component.

        Args:
            component_id: ID of the component
            material_id: ID of the material to remove

        Returns:
            bool: True if the material was removed successfully

        Raises:
            NotFoundError: If the component or component-material association does not exist
        """
        pass