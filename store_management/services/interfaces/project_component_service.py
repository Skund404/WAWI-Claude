# services/interfaces/project_component_service.py
"""
Interface for Project Component Service in the leatherworking application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from database.models.components import ProjectComponent
from database.models.picking_list import PickingListItem


class IProjectComponentService(ABC):
    """
    Abstract base class defining the interface for Project Component Service.
    Handles operations related to components within a specific project.
    """

    @abstractmethod
    def add_component_to_project(
        self,
        project_id: int,
        component_id: int,
        quantity: int = 1,
        **kwargs
    ) -> ProjectComponent:
        """
        Add a component to a project.

        Args:
            project_id (int): ID of the project
            component_id (int): ID of the component
            quantity (int): Quantity of the component in the project
            **kwargs: Additional attributes for the project component

        Returns:
            ProjectComponent: The created project component association
        """
        pass

    @abstractmethod
    def get_project_components(self, project_id: int) -> List[ProjectComponent]:
        """
        Retrieve all components for a specific project.

        Args:
            project_id (int): ID of the project

        Returns:
            List[ProjectComponent]: List of components in the project
        """
        pass

    @abstractmethod
    def update_project_component(
        self,
        project_component_id: int,
        quantity: Optional[int] = None,
        **kwargs
    ) -> ProjectComponent:
        """
        Update a project component.

        Args:
            project_component_id (int): ID of the project component
            quantity (Optional[int]): New quantity of the component
            **kwargs: Additional attributes to update

        Returns:
            ProjectComponent: The updated project component
        """
        pass

    @abstractmethod
    def remove_component_from_project(
        self,
        project_component_id: int
    ) -> bool:
        """
        Remove a component from a project.

        Args:
            project_component_id (int): ID of the project component to remove

        Returns:
            bool: True if removal was successful, False otherwise
        """
        pass

    @abstractmethod
    def link_project_component_to_picking_list_item(
        self,
        project_component_id: int,
        picking_list_item_id: int
    ) -> ProjectComponent:
        """
        Link a project component to a picking list item.

        Args:
            project_component_id (int): ID of the project component
            picking_list_item_id (int): ID of the picking list item

        Returns:
            ProjectComponent: The updated project component with picking list item link
        """
        pass