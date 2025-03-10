# services/interfaces/project_service.py
# Protocol definition for project service

from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IProjectService(Protocol):
    """Interface for project-related operations."""

    def get_by_id(self, project_id: int) -> Dict[str, Any]:
        """Get project by ID.

        Args:
            project_id: ID of the project to retrieve

        Returns:
            Dict representing the project

        Raises:
            NotFoundError: If project not found
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all projects, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing projects
        """
        ...

    def create(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project.

        Args:
            project_data: Dict containing project properties

        Returns:
            Dict representing the created project

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update(self, project_id: int, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project.

        Args:
            project_id: ID of the project to update
            project_data: Dict containing updated project properties

        Returns:
            Dict representing the updated project

        Raises:
            NotFoundError: If project not found
            ValidationError: If validation fails
        """
        ...

    def delete(self, project_id: int) -> bool:
        """Delete a project by ID.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If project not found
        """
        ...

    def add_component(self, project_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add component to project.

        Args:
            project_id: ID of the project
            component_data: Dict containing component properties

        Returns:
            Dict representing the created project component

        Raises:
            NotFoundError: If project or component not found
            ValidationError: If validation fails
        """
        ...

    def remove_component(self, project_id: int, component_id: int) -> bool:
        """Remove component from project.

        Args:
            project_id: ID of the project
            component_id: ID of the component

        Returns:
            True if successful

        Raises:
            NotFoundError: If project or component not found
        """
        ...

    def update_component(self, project_id: int, component_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update component in project.

        Args:
            project_id: ID of the project
            component_id: ID of the component
            data: Dict containing updated component properties

        Returns:
            Dict representing the updated component

        Raises:
            NotFoundError: If project or component not found
            ValidationError: If validation fails
        """
        ...

    def generate_picking_list(self, project_id: int) -> Dict[str, Any]:
        """Generate picking list for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dict representing the generated picking list

        Raises:
            NotFoundError: If project not found
            ValidationError: If validation fails
        """
        ...

    def generate_tool_list(self, project_id: int) -> Dict[str, Any]:
        """Generate tool list for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dict representing the generated tool list

        Raises:
            NotFoundError: If project not found
            ValidationError: If validation fails
        """
        ...

    def calculate_cost(self, project_id: int) -> Dict[str, Any]:
        """Calculate total cost for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dict with cost breakdown

        Raises:
            NotFoundError: If project not found
        """
        ...

    def update_status(self, project_id: int, status: str) -> Dict[str, Any]:
        """Update project status.

        Args:
            project_id: ID of the project
            status: New status

        Returns:
            Dict representing the updated project

        Raises:
            NotFoundError: If project not found
            ValidationError: If validation fails
        """
        ...

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get projects by customer ID.

        Args:
            customer_id: ID of the customer

        Returns:
            List of projects for the specified customer
        """
        ...

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get projects within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of projects within the specified date range
        """
        ...