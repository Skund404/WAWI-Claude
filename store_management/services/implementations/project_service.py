# services/implementations/project_service.py
# Implementation of the project service interface

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.project_repository import ProjectRepository
from database.repositories.project_component_repository import ProjectComponentRepository
from database.repositories.component_repository import ComponentRepository
from database.repositories.picking_list_repository import PickingListRepository
from database.repositories.tool_list_repository import ToolListRepository
from database.models.enums import ProjectStatus, PickingListStatus, ToolListStatus
from services.base_service import BaseService
from services.exceptions import ValidationError, NotFoundError
from services.dto.project_dto import ProjectDTO
from services.dto.picking_list_dto import PickingListDTO
from services.dto.tool_list_dto import ToolListDTO

from di.inject import inject


class ProjectService(BaseService):
    """Implementation of the project service interface."""

    @inject
    def __init__(self, session: Session,
                 project_repository: Optional[ProjectRepository] = None,
                 project_component_repository: Optional[ProjectComponentRepository] = None,
                 component_repository: Optional[ComponentRepository] = None,
                 picking_list_repository: Optional[PickingListRepository] = None,
                 tool_list_repository: Optional[ToolListRepository] = None):
        """Initialize the project service.

        Args:
            session: SQLAlchemy database session
            project_repository: Optional ProjectRepository instance
            project_component_repository: Optional ProjectComponentRepository instance
            component_repository: Optional ComponentRepository instance
            picking_list_repository: Optional PickingListRepository instance
            tool_list_repository: Optional ToolListRepository instance
        """
        super().__init__(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.project_component_repository = project_component_repository or ProjectComponentRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.picking_list_repository = picking_list_repository or PickingListRepository(session)
        self.tool_list_repository = tool_list_repository or ToolListRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, project_id: int) -> Dict[str, Any]:
        """Get project by ID.

        Args:
            project_id: ID of the project to retrieve

        Returns:
            Dict representing the project

        Raises:
            NotFoundError: If project not found
        """
        try:
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")
            return ProjectDTO.from_model(project).to_dict()
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving project {project_id}: {str(e)}")
            raise

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all projects, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing projects
        """
        try:
            projects = self.project_repository.get_all(filters)
            return [ProjectDTO.from_model(project).to_dict() for project in projects]
        except Exception as e:
            self.logger.error(f"Error retrieving projects: {str(e)}")
            raise

    def create(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project.

        Args:
            project_data: Dict containing project properties

        Returns:
            Dict representing the created project

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate project data
            self._validate_project_data(project_data)

            # Create project
            with self.transaction():
                # Set default status if not provided
                if 'status' not in project_data:
                    project_data['status'] = ProjectStatus.INITIAL_CONSULTATION.value

                # Set timestamps if not provided
                now = datetime.now()
                if 'start_date' not in project_data:
                    project_data['start_date'] = now

                # Extract components before creating project
                components = project_data.pop('components', [])

                project = self.project_repository.create(project_data)

                # Add components if provided
                for component_data in components:
                    component_data['project_id'] = project.id
                    self.project_component_repository.create(component_data)

                return ProjectDTO.from_model(project).to_dict()
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating project: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Validate project data
            self._validate_project_data(project_data, update=True)

            # Update project
            with self.transaction():
                updated_project = self.project_repository.update(project_id, project_data)
                return ProjectDTO.from_model(updated_project).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating project {project_id}: {str(e)}")
            raise

    def delete(self, project_id: int) -> bool:
        """Delete a project by ID.

        Args:
            project_id: ID of the project to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If project not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Delete project
            with self.transaction():
                # Delete project components first
                project_components = self.project_component_repository.get_by_project(project_id)
                for component in project_components:
                    self.project_component_repository.delete(component.id)

                # Delete picking lists
                picking_lists = self.picking_list_repository.get_by_project(project_id)
                for picking_list in picking_lists:
                    self.picking_list_repository.delete(picking_list.id)

                # Delete tool lists
                tool_lists = self.tool_list_repository.get_by_project(project_id)
                for tool_list in tool_lists:
                    self.tool_list_repository.delete(tool_list.id)

                # Then delete project
                self.project_repository.delete(project_id)
                return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id}: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Check if component exists
            component_id = component_data.get('component_id')
            if component_id:
                component = self.component_repository.get_by_id(component_id)
                if not component:
                    raise NotFoundError(f"Component with ID {component_id} not found")

            # Add project_id to data
            component_data['project_id'] = project_id

            # Validate component data
            self._validate_component_data(component_data)

            # Create project component
            with self.transaction():
                project_component = self.project_component_repository.create(component_data)
                return self._to_dict(project_component)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adding component to project {project_id}: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Find project component
            project_components = self.project_component_repository.get_by_project(project_id)
            project_component = next((pc for pc in project_components if pc.component_id == component_id), None)
            if not project_component:
                raise NotFoundError(f"Component {component_id} not found in project {project_id}")

            # Delete project component
            with self.transaction():
                self.project_component_repository.delete(project_component.id)
                return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error removing component {component_id} from project {project_id}: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Find project component
            project_components = self.project_component_repository.get_by_project(project_id)
            project_component = next((pc for pc in project_components if pc.component_id == component_id), None)
            if not project_component:
                raise NotFoundError(f"Component {component_id} not found in project {project_id}")

            # Update project component
            with self.transaction():
                updated_component = self.project_component_repository.update(project_component.id, data)
                return self._to_dict(updated_component)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating component {component_id} in project {project_id}: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Get project components
            project_components = self.project_component_repository.get_by_project(project_id)
            if not project_components:
                raise ValidationError(f"Project {project_id} has no components")

            # Create picking list
            with self.transaction():
                picking_list_data = {
                    'project_id': project_id,
                    'status': PickingListStatus.DRAFT.value,
                    'created_at': datetime.now()
                }
                picking_list = self.picking_list_repository.create(picking_list_data)

                # Add picking list items
                for project_component in project_components:
                    component = self.component_repository.get_by_id(project_component.component_id)
                    if component:
                        # Get materials for component
                        for material in component.materials:
                            picking_list_item_data = {
                                'picking_list_id': picking_list.id,
                                'component_id': component.id,
                                'material_id': material.id,
                                'quantity_ordered': material.quantity * project_component.quantity,
                                'quantity_picked': 0
                            }
                            self.picking_list_repository.add_item(picking_list_item_data)

                return PickingListDTO.from_model(picking_list).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error generating picking list for project {project_id}: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Create tool list
            with self.transaction():
                tool_list_data = {
                    'project_id': project_id,
                    'status': ToolListStatus.DRAFT.value,
                    'created_at': datetime.now()
                }
                tool_list = self.tool_list_repository.create(tool_list_data)

                # Get recommended tools for project type
                tools = self.tool_list_repository.get_recommended_tools_for_project(project.type)

                # Add tool list items
                for tool in tools:
                    tool_list_item_data = {
                        'tool_list_id': tool_list.id,
                        'tool_id': tool.id,
                        'quantity': 1
                    }
                    self.tool_list_repository.add_item(tool_list_item_data)

                return ToolListDTO.from_model(tool_list).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error generating tool list for project {project_id}: {str(e)}")
            raise

    def calculate_cost(self, project_id: int) -> Dict[str, Any]:
        """Calculate total cost for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dict with cost breakdown

        Raises:
            NotFoundError: If project not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Calculate material costs
            material_costs = self.project_repository.calculate_material_costs(project_id)

            # Calculate labor costs (if applicable)
            labor_costs = self.project_repository.calculate_labor_costs(project_id)

            # Calculate overhead costs (if applicable)
            overhead_costs = self.project_repository.calculate_overhead_costs(project_id)

            # Calculate total cost
            total_cost = material_costs + labor_costs + overhead_costs

            return {
                'project_id': project_id,
                'material_costs': material_costs,
                'labor_costs': labor_costs,
                'overhead_costs': overhead_costs,
                'total_cost': total_cost
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error calculating cost for project {project_id}: {str(e)}")
            raise

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
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Validate status
            self._validate_enum_value(ProjectStatus, status, "project status")

            # Update project status
            with self.transaction():
                project_data = {'status': status}

                # Update end date if status is COMPLETED
                if status == ProjectStatus.COMPLETED.value:
                    project_data['end_date'] = datetime.now()

                updated_project = self.project_repository.update(project_id, project_data)

                # Log status change in project history
                history_data = {
                    'project_id': project_id,
                    'status': status,
                    'timestamp': datetime.now(),
                    'notes': 'Status updated via service'
                }
                self.project_repository.add_status_history(history_data)

                return ProjectDTO.from_model(updated_project).to_dict()
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating status for project {project_id}: {str(e)}")
            raise

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get projects by customer ID.

        Args:
            customer_id: ID of the customer

        Returns:
            List of projects for the specified customer
        """
        try:
            projects = self.project_repository.get_by_customer(customer_id)
            return [ProjectDTO.from_model(project).to_dict() for project in projects]
        except Exception as e:
            self.logger.error(f"Error retrieving projects for customer {customer_id}: {str(e)}")
            raise

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get projects within a date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of projects within the specified date range
        """
        try:
            projects = self.project_repository.get_by_date_range(start_date, end_date)
            return [ProjectDTO.from_model(project).to_dict() for project in projects]
        except Exception as e:
            self.logger.error(f"Error retrieving projects within date range: {str(e)}")
            raise

    # Helper methods

    def _validate_project_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate project data.

        Args:
            data: Project data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['name', 'type']
        self._validate_required_fields(data, required_fields, update)

        # Validate project type
        if 'type' in data:
            from database.models.enums import ProjectType
            self._validate_enum_value(ProjectType, data['type'], "project type")

        # Validate project status
        if 'status' in data:
            from database.models.enums import ProjectStatus
            self._validate_enum_value(ProjectStatus, data['status'], "project status")

    def _validate_component_data(self, data: Dict[str, Any]) -> None:
        """Validate component data.

        Args:
            data: Component data to validate

        Raises:
            ValidationError: If validation fails
        """
        required_fields = ['component_id', 'quantity']
        self._validate_required_fields(data, required_fields)

        # Validate quantity
        if 'quantity' in data and data['quantity'] <= 0:
            raise ValidationError(f"Quantity must be greater than zero")