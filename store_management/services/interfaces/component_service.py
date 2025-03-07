# services/interfaces/component_service.py
from abc import ABC, abstractmethod
from database.models.components import Component
from database.models.enums import ComponentType
from typing import Any, Dict, List, Optional
from datetime import datetime

class IComponentService(ABC):
    """
    Interface defining operations for Component management in the leatherworking application.
    """

    @abstractmethod
    def create_component(
        self,
        name: str,
        description: Optional[str] = None,
        component_type: Optional[ComponentType] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> Component:
        """
        Create a new component with specified details.

        Args:
            name: Name of the component
            description: Optional description of the component
            component_type: Type of the component
            attributes: Optional JSON-compatible attributes for the component

        Returns:
            The created Component instance
        """
        pass

    @abstractmethod
    def get_component_by_id(self, component_id: int) -> Optional[Component]:
        """
        Retrieve a component by its unique identifier.

        Args:
            component_id: Unique identifier of the component

        Returns:
            Component instance or None if not found
        """
        pass

    @abstractmethod
    def update_component(
        self,
        component_id: int,
        updates: Dict[str, Any]
    ) -> Optional[Component]:
        """
        Update an existing component's details.

        Args:
            component_id: Unique identifier of the component
            updates: Dictionary of attributes to update

        Returns:
            Updated Component instance or None if update failed
        """
        pass

    @abstractmethod
    def delete_component(self, component_id: int) -> bool:
        """
        Delete a component by its unique identifier.

        Args:
            component_id: Unique identifier of the component

        Returns:
            Boolean indicating successful deletion
        """
        pass

    @abstractmethod
    def list_components(
        self,
        component_type: Optional[ComponentType] = None,
        **filters
    ) -> List[Component]:
        """
        List components with optional filtering.

        Args:
            component_type: Optional filter by component type
            **filters: Additional optional filters

        Returns:
            List of matching Component instances
        """
        pass

    @abstractmethod
    def associate_materials(
        self,
        component_id: int,
        material_ids: List[int],
        quantities: Optional[List[float]] = None
    ) -> bool:
        """
        Associate materials with a component.

        Args:
            component_id: ID of the component
            material_ids: List of material IDs to associate
            quantities: Optional list of quantities corresponding to materials

        Returns:
            Boolean indicating successful association
        """
        pass

    @abstractmethod
    def get_component_materials(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Retrieve materials associated with a specific component.

        Args:
            component_id: ID of the component

        Returns:
            List of dictionaries containing material details
        """
        pass