# services/implementations/project_service.py
from typing import List, Optional, Dict, Any, Type, cast
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from database.repositories.project_repository import ProjectRepository
from database.repositories.project_component_repository import ProjectComponentRepository
from database.repositories.component_repository import ComponentRepository
from database.repositories.picking_list_repository import PickingListRepository
from database.repositories.picking_list_item_repository import PickingListItemRepository
from database.repositories.tool_list_repository import ToolListRepository
from database.repositories.tool_list_item_repository import ToolListItemRepository
from database.repositories.material_repository import MaterialRepository
from database.repositories.inventory_repository import InventoryRepository
from database.models.enums import ProjectStatus, ProjectType, PickingListStatus, ToolListStatus
from services.base_service import BaseService, ValidationError, NotFoundError


class ProjectService(BaseService):
    """Implementation of the project service interface."""

    def __init__(self, session: Session,
                 project_repository: Optional[ProjectRepository] = None,
                 project_component_repository: Optional[ProjectComponentRepository] = None,
                 component_repository: Optional[ComponentRepository] = None,
                 picking_list_repository: Optional[PickingListRepository] = None,
                 picking_list_item_repository: Optional[PickingListItemRepository] = None,
                 tool_list_repository: Optional[ToolListRepository] = None,
                 tool_list_item_repository: Optional[ToolListItemRepository] = None,
                 material_repository: Optional[MaterialRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None):
        """Initialize the project service.

        Args:
            session: SQLAlchemy database session
            project_repository: Optional ProjectRepository instance
            project_component_repository: Optional ProjectComponentRepository instance
            component_repository: Optional ComponentRepository instance
            picking_list_repository: Optional PickingListRepository instance
            picking_list_item_repository: Optional PickingListItemRepository instance
            tool_list_repository: Optional ToolListRepository instance
            tool_list_item_repository: Optional ToolListItemRepository instance
            material_repository: Optional MaterialRepository instance
            inventory_repository: Optional InventoryRepository instance
        """
        super().__init__(session)
        self.project_repository = project_repository or ProjectRepository(session)
        self.project_component_repository = project_component_repository or ProjectComponentRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.picking_list_repository = picking_list_repository or PickingListRepository(session)
        self.picking_list_item_repository = picking_list_item_repository or PickingListItemRepository(session)
        self.tool_list_repository = tool_list_repository or ToolListRepository(session)
        self.tool_list_item_repository = tool_list_item_repository or ToolListItemRepository(session)
        self.material_repository = material_repository or MaterialRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)

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

            # Get project components
            project_dict = self._to_dict(project)
            project_components = self.project_component_repository.get_by_project(project_id)
            project_dict['components'] = [self._to_dict(pc) for pc in project_components]

            return project_dict
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
            project_dicts = []

            for project in projects:
                project_dict = self._to_dict(project)
                # Get project components count (for efficiency, we don't load all components)
                component_count = self.project_component_repository.count_by_project(project.id)
                project_dict['component_count'] = component_count
                project_dicts.append(project_dict)

            return project_dicts
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

            # Extract components data if present
            components_data = project_data.pop('components', [])

            # Create project
            with self.transaction():
                # Set default status if not provided
                if 'status' not in project_data:
                    project_data['status'] = ProjectStatus.INITIAL_CONSULTATION.value

                # Set timestamps if not provided
                now = datetime.now()
                if 'start_date' not in project_data:
                    project_data['start_date'] = now

                project = self.project_repository.create(project_data)

                # Add components if provided
                for component_data in components_data:
                    component_data['project_id'] = project.id
                    self.project_component_repository.create(component_data)

                # Prepare response
                project_dict = self._to_dict(project)
                project_dict['components'] = []

                for component_data in components_data:
                    component_data['project_id'] = project.id
                    project_dict['components'].append(component_data)

                return project_dict
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

                # Get project components
                project_dict = self._to_dict(updated_project)
                project_components = self.project_component_repository.get_by_project(project_id)
                project_dict['components'] = [self._to_dict(pc) for pc in project_components]

                return project_dict
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

            # Delete project and related records
            with self.transaction():
                # Delete project components
                project_components = self.project_component_repository.get_by_project(project_id)
                for pc in project_components:
                    self.project_component_repository.delete(pc.id)

                # Delete picking lists and items
                picking_lists = self.picking_list_repository.get_by_project(project_id)
                for pl in picking_lists:
                    picking_list_items = self.picking_list_item_repository.get_by_picking_list(pl.id)
                    for pli in picking_list_items:
                        self.picking_list_item_repository.delete(pli.id)
                    self.picking_list_repository.delete(pl.id)

                # Delete tool lists and items
                tool_lists = self.tool_list_repository.get_by_project(project_id)
                for tl in tool_lists:
                    tool_list_items = self.tool_list_item_repository.get_by_tool_list(tl.id)
                    for tli in tool_list_items:
                        self.tool_list_item_repository.delete(tli.id)
                    self.tool_list_repository.delete(tl.id)

                # Delete project
                self.project_repository.delete(project_id)
                return True
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

            # Validate component data
            self._validate_component_data(component_data)

            # Add component to project
            with self.transaction():
                component_data['project_id'] = project_id
                project_component = self.project_component_repository.create(component_data)

                # Return project component with component details
                project_component_dict = self._to_dict(project_component)

                if component_id:
                    component = self.component_repository.get_by_id(component_id)
                    project_component_dict['component'] = self._to_dict(component)

                return project_component_dict
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

            # Remove component from project
            with self.transaction():
                self.project_component_repository.delete(project_component.id)
                return True
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
            Dict representing the updated project component

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

            # Validate component data
            self._validate_component_data(data, update=True)

            # Update component in project
            with self.transaction():
                updated_project_component = self.project_component_repository.update(project_component.id, data)

                # Return project component with component details
                project_component_dict = self._to_dict(updated_project_component)
                component = self.component_repository.get_by_id(component_id)
                project_component_dict['component'] = self._to_dict(component)

                return project_component_dict
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

            # Generate picking list
            with self.transaction():
                # Create picking list
                picking_list_data = {
                    'project_id': project_id,
                    'status': PickingListStatus.DRAFT.value,
                    'created_at': datetime.now()
                }
                picking_list = self.picking_list_repository.create(picking_list_data)

                # Get materials for each component
                for project_component in project_components:
                    component = self.component_repository.get_by_id(project_component.component_id)
                    if not component:
                        continue

                    # Get materials for component
                    component_materials = getattr(component, 'materials', [])

                    for component_material in component_materials:
                        material = self.material_repository.get_by_id(component_material.material_id)
                        if not material:
                            continue

                        # Calculate required quantity
                        quantity = component_material.quantity * project_component.quantity

                        # Add to picking list
                        picking_list_item_data = {
                            'picking_list_id': picking_list.id,
                            'component_id': component.id,
                            'material_id': material.id,
                            'quantity_ordered': quantity,
                            'quantity_picked': 0
                        }
                        self.picking_list_item_repository.create(picking_list_item_data)

                # Get complete picking list with items
                picking_list_dict = self._to_dict(picking_list)
                picking_list_items = self.picking_list_item_repository.get_by_picking_list(picking_list.id)
                picking_list_dict['items'] = [self._to_dict(item) for item in picking_list_items]

                return picking_list_dict
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

            # Get project components
            project_components = self.project_component_repository.get_by_project(project_id)
            if not project_components:
                raise ValidationError(f"Project {project_id} has no components")

            # Generate tool list
            with self.transaction():
                # Create tool list
                tool_list_data = {
                    'project_id': project_id,
                    'status': ToolListStatus.DRAFT.value,
                    'created_at': datetime.now()
                }
                tool_list = self.tool_list_repository.create(tool_list_data)

                # Get tools for project type
                # Note: This is a simplified implementation. In reality, you would need
                # to determine required tools based on component types, materials, etc.
                tool_requirements = self._get_tools_for_project_type(project.type)

                # Add tools to tool list
                for tool_id, quantity in tool_requirements.items():
                    tool_list_item_data = {
                        'tool_list_id': tool_list.id,
                        'tool_id': tool_id,
                        'quantity': quantity
                    }
                    self.tool_list_item_repository.create(tool_list_item_data)

                # Get complete tool list with items
                tool_list_dict = self._to_dict(tool_list)
                tool_list_items = self.tool_list_item_repository.get_by_tool_list(tool_list.id)
                tool_list_dict['items'] = [self._to_dict(item) for item in tool_list_items]

                return tool_list_dict
        except Exception as e:
            self.logger.error(f"Error generating tool list for project {project_id}: {str(e)}")
            raise

    def calculate_cost(self, project_id: int) -> Dict[str, Any]:
        """Calculate total cost for a project.

        Args:
            project_id: ID of the project

        Returns:
            Dict with cost information

        Raises:
            NotFoundError: If project not found
        """
        try:
            # Check if project exists
            project = self.project_repository.get_by_id(project_id)
            if not project:
                raise NotFoundError(f"Project with ID {project_id} not found")

            # Get project components
            project_components = self.project_component_repository.get_by_project(project_id)

            # Calculate material costs
            material_costs = 0.0
            materials_breakdown = []

            for project_component in project_components:
                component = self.component_repository.get_by_id(project_component.component_id)
                if not component:
                    continue

                # Get materials for component
                component_materials = getattr(component, 'materials', [])

                for component_material in component_materials:
                    material = self.material_repository.get_by_id(component_material.material_id)
                    if not material or not hasattr(material, 'price_per_unit') or material.price_per_unit is None:
                        continue

                    # Calculate cost for this material
                    quantity = component_material.quantity * project_component.quantity
                    cost = material.price_per_unit * quantity

                    material_costs += cost
                    materials_breakdown.append({
                        'material_id': material.id,
                        'material_name': material.name,
                        'component_id': component.id,
                        'component_name': component.name,
                        'quantity': quantity,
                        'price_per_unit': material.price_per_unit,
                        'cost': cost
                    })

            # Calculate labor costs (simplified - would be more complex in reality)
            labor_hours = self._estimate_labor_hours(project)
            labor_rate = 25.0  # This would typically come from configuration
            labor_cost = labor_hours * labor_rate

            # Calculate overhead costs (simplified)
            overhead_rate = 0.15  # 15% overhead
            overhead_cost = (material_costs + labor_cost) * overhead_rate

            # Calculate total cost
            total_cost = material_costs + labor_cost + overhead_cost

            # Return cost breakdown
            return {
                'project_id': project_id,
                'material_costs': material_costs,
                'materials_breakdown': materials_breakdown,
                'labor_hours': labor_hours,
                'labor_rate': labor_rate,
                'labor_cost': labor_cost,
                'overhead_rate': overhead_rate,
                'overhead_cost': overhead_cost,
                'total_cost': total_cost
            }
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
            try:
                ProjectStatus(status)
            except ValueError:
                raise ValidationError(f"Invalid project status: {status}")

            # Update project status
            with self.transaction():
                project_data = {'status': status}

                # Set end_date if project is completed
                if status == ProjectStatus.COMPLETED.value:
                    project_data['end_date'] = datetime.now()

                updated_project = self.project_repository.update(project_id, project_data)
                return self._to_dict(updated_project)
        except Exception as e:
            self.logger.error(f"Error updating status for project {project_id}: {str(e)}")
            raise

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get projects by customer ID.

        Args:
            customer_id: ID of the customer

        Returns:
            List of dicts representing projects for the customer
        """
        try:
            # Get projects by customer
            projects = self.project_repository.get_by_customer(customer_id)
            project_dicts = []

            for project in projects:
                project_dict = self._to_dict(project)
                # Get project components count
                component_count = self.project_component_repository.count_by_project(project.id)
                project_dict['component_count'] = component_count
                project_dicts.append(project_dict)

            return project_dicts
        except Exception as e:
            self.logger.error(f"Error getting projects for customer {customer_id}: {str(e)}")
            raise

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get projects within a date range.

        Args:
            start_date: Start date
            end_date: End date

        Returns:
            List of dicts representing projects in the date range
        """
        try:
            # Validate date range
            if start_date > end_date:
                raise ValidationError(f"Start date must be before end date")

            # Get projects by date range
            projects = self.project_repository.get_by_date_range(start_date, end_date)
            project_dicts = []

            for project in projects:
                project_dict = self._to_dict(project)
                # Get project components count
                component_count = self.project_component_repository.count_by_project(project.id)
                project_dict['component_count'] = component_count
                project_dicts.append(project_dict)

            return project_dicts
        except Exception as e:
            self.logger.error(f"Error getting projects in date range: {str(e)}")
            raise

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for projects by query string.

        Args:
            query: Search query string

        Returns:
            List of dicts representing matching projects
        """
        try:
            # Search projects
            projects = self.project_repository.search(query)
            project_dicts = []

            for project in projects:
                project_dict = self._to_dict(project)
                # Get project components count
                component_count = self.project_component_repository.count_by_project(project.id)
                project_dict['component_count'] = component_count
                project_dicts.append(project_dict)

            return project_dicts
        except Exception as e:
            self.logger.error(f"Error searching projects: {str(e)}")
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
        # Only check required fields for new projects
        if not update:
            required_fields = ['name', 'type']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate project type if provided
        if 'type' in data:
            try:
                ProjectType(data['type'])
            except ValueError:
                raise ValidationError(f"Invalid project type: {data['type']}")

        # Validate project status if provided
        if 'status' in data:
            try:
                ProjectStatus(data['status'])
            except ValueError:
                raise ValidationError(f"Invalid project status: {data['status']}")

        # Validate dates
        if 'start_date' in data and 'end_date' in data and data['end_date'] is not None:
            if data['start_date'] > data['end_date']:
                raise ValidationError(f"Start date must be before end date")

    def _validate_component_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate component data.

        Args:
            data: Component data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Only check required fields for new components
        if not update:
            required_fields = ['component_id', 'quantity']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate quantity if provided
        if 'quantity' in data:
            quantity = data['quantity']
            if not isinstance(quantity, (int, float)) or quantity <= 0:
                raise ValidationError(f"Quantity must be greater than zero")

    def _get_tools_for_project_type(self, project_type: str) -> Dict[int, int]:
        """Get required tools for a project type.

        Args:
            project_type: Project type

        Returns:
            Dict mapping tool IDs to quantities
        """
        # This is a simplified implementation. In reality, this would query a
        # configuration database or use a more sophisticated algorithm to determine
        # required tools based on project type, components, etc.

        # For now, return a placeholder implementation
        tools = {}

        # In a real implementation, you would query the database for tools
        # required for this project type
        # Example: Get cutting tools for wallet projects
        if project_type == ProjectType.WALLET.value:
            cutting_tools = self.tool_list_repository.get_tools_by_category("CUTTING")
            for tool in cutting_tools:
                tools[tool.id] = 1

        # Add generic tools that are always needed
        common_tools = self.tool_list_repository.get_common_tools()
        for tool in common_tools:
            tools[tool.id] = 1

        return tools

    def _estimate_labor_hours(self, project) -> float:
        """Estimate labor hours for a project.

        Args:
            project: Project object

        Returns:
            Estimated labor hours
        """
        # This is a simplified implementation. In reality, labor estimation would
        # be much more complex, considering component types, quantities, etc.

        # Base hours by project type
        base_hours = {
            ProjectType.WALLET.value: 4.0,
            ProjectType.BELT.value: 2.0,
            ProjectType.MESSENGER_BAG.value: 12.0,
            ProjectType.BACKPACK.value: 16.0,
            ProjectType.WATCH_STRAP.value: 1.5,
            # Add more project types as needed
        }

        # Get base hours for this project type
        hours = base_hours.get(project.type, 8.0)  # Default to 8 hours

        # Adjust based on components
        component_count = self.project_component_repository.count_by_project(project.id)
        hours += component_count * 0.5  # Add 0.5 hours per component

        return hours