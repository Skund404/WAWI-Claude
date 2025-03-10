# database/repositories/project_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Union
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc, case, text

from database.models.project import Project
from database.models.project_component import ProjectComponent
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import ProjectStatus, ProjectType


class ProjectRepository(BaseRepository[Project]):
    """Repository for project operations.

    This repository provides methods for managing project data, including
    components, status tracking, and project planning.
    """

    def _get_model_class(self) -> Type[Project]:
        """Return the model class this repository manages.

        Returns:
            The Project model class
        """
        return Project

    # Basic query methods

    def get_by_status(self, status: ProjectStatus) -> List[Project]:
        """Get projects by status.

        Args:
            status: Project status to filter by

        Returns:
            List of project instances with the specified status
        """
        self.logger.debug(f"Getting projects with status '{status.value}'")
        return self.session.query(Project).filter(Project.status == status).all()

    def get_by_type(self, project_type: ProjectType) -> List[Project]:
        """Get projects by type.

        Args:
            project_type: Project type to filter by

        Returns:
            List of project instances with the specified type
        """
        self.logger.debug(f"Getting projects with type '{project_type.value}'")
        return self.session.query(Project).filter(Project.type == project_type).all()

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Project]:
        """Get projects in date range.

        Args:
            start_date: Start date for the range
            end_date: End date for the range

        Returns:
            List of project instances within the date range
        """
        self.logger.debug(f"Getting projects between {start_date} and {end_date}")
        return self.session.query(Project). \
            filter(Project.start_date >= start_date). \
            filter(Project.start_date <= end_date).all()

    def get_by_customer(self, customer_id: int) -> List[Project]:
        """Get projects for customer.

        Args:
            customer_id: ID of the customer

        Returns:
            List of project instances for the specified customer
        """
        self.logger.debug(f"Getting projects for customer {customer_id}")
        # Check if sales_id is used as a link to customer or if customer_id is directly on project
        if hasattr(Project, 'customer_id'):
            return self.session.query(Project).filter(Project.customer_id == customer_id).all()
        else:
            from database.models.sales import Sales
            return self.session.query(Project). \
                join(Sales, Project.sales_id == Sales.id). \
                filter(Sales.customer_id == customer_id).all()

    def get_active_projects(self) -> List[Project]:
        """Get all active projects (not completed or cancelled).

        Returns:
            List of active project instances
        """
        self.logger.debug("Getting active projects")
        # Define statuses that are considered active
        active_statuses = [
            ProjectStatus.INITIAL_CONSULTATION,
            ProjectStatus.DESIGN_PHASE,
            ProjectStatus.PATTERN_DEVELOPMENT,
            ProjectStatus.CLIENT_APPROVAL,
            ProjectStatus.MATERIAL_SELECTION,
            ProjectStatus.MATERIAL_PURCHASED,
            ProjectStatus.CUTTING,
            ProjectStatus.SKIVING,
            ProjectStatus.PREPARATION,
            ProjectStatus.ASSEMBLY,
            ProjectStatus.STITCHING,
            ProjectStatus.EDGE_FINISHING,
            ProjectStatus.HARDWARE_INSTALLATION,
            ProjectStatus.CONDITIONING,
            ProjectStatus.QUALITY_CHECK,
            ProjectStatus.FINAL_TOUCHES,
            ProjectStatus.PHOTOGRAPHY,
            ProjectStatus.PACKAGING,
            ProjectStatus.PLANNED,
            ProjectStatus.MATERIALS_READY,
            ProjectStatus.IN_PROGRESS,
            ProjectStatus.ON_HOLD
        ]
        return self.session.query(Project).filter(Project.status.in_(active_statuses)).all()

    def get_overdue_projects(self) -> List[Project]:
        """Get projects past their end date but not completed.

        Returns:
            List of overdue project instances
        """
        self.logger.debug("Getting overdue projects")
        completed_statuses = [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]

        return self.session.query(Project). \
            filter(Project.end_date < datetime.now()). \
            filter(~Project.status.in_(completed_statuses)).all()

    def get_upcoming_projects(self, days: int = 14) -> List[Project]:
        """Get projects scheduled to start soon.

        Args:
            days: Number of days to look ahead

        Returns:
            List of upcoming project instances
        """
        self.logger.debug(f"Getting projects starting in the next {days} days")
        now = datetime.now()
        future = now + timedelta(days=days)

        return self.session.query(Project). \
            filter(Project.start_date > now). \
            filter(Project.start_date <= future).all()

    def count_projects_by_status(self) -> Dict[str, int]:
        """Count projects by status.

        Returns:
            Dictionary mapping status values to counts
        """
        self.logger.debug("Counting projects by status")

        results = self.session.query(
            Project.status,
            func.count().label('count')
        ).group_by(Project.status).all()

        return {status.value: count for status, count in results}

    # Component-related methods

    def get_project_with_components(self, project_id: int) -> Dict[str, Any]:
        """Get project with all components.

        Args:
            project_id: ID of the project

        Returns:
            Project dictionary with components and related information

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Getting project {project_id} with components")
        from database.models.component import Component

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        # Get project data
        result = project.to_dict()

        # Get project components
        components_query = self.session.query(ProjectComponent, Component). \
            join(Component, ProjectComponent.component_id == Component.id). \
            filter(ProjectComponent.project_id == project_id)

        components = []
        for project_component, component in components_query.all():
            component_dict = component.to_dict()
            component_dict['project_component_id'] = project_component.id
            component_dict['quantity'] = project_component.quantity
            components.append(component_dict)

        result['components'] = components

        # Get related information
        if hasattr(project, 'sales_id') and project.sales_id:
            from database.models.sales import Sales
            sales = self.session.query(Sales).get(project.sales_id)
            if sales:
                result['sales'] = sales.to_dict()

        return result

    def create_project_with_components(self, project_data: Dict[str, Any],
                                       components: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create project with components.

        Args:
            project_data: Project data dictionary
            components: List of component dictionaries with component_id and quantity

        Returns:
            Created project with components

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug("Creating project with components")
        from database.models.component import Component

        try:
            # Create project
            project = Project(**project_data)
            created_project = self.create(project)

            # Add components
            project_components = []
            for comp_data in components:
                # Verify component exists
                component_id = comp_data['component_id']
                component = self.session.query(Component).get(component_id)
                if not component:
                    raise ValidationError(f"Component with ID {component_id} not found")

                # Create project component
                project_component = ProjectComponent(
                    project_id=created_project.id,
                    component_id=component_id,
                    quantity=comp_data.get('quantity', 1)
                )
                self.session.add(project_component)
                project_components.append(project_component)

            # Flush to get IDs
            self.session.flush()

            # Prepare result
            result = created_project.to_dict()
            result['components'] = []

            for pc in project_components:
                component = self.session.query(Component).get(pc.component_id)
                if component:
                    component_dict = component.to_dict()
                    component_dict['project_component_id'] = pc.id
                    component_dict['quantity'] = pc.quantity
                    result['components'].append(component_dict)

            return result
        except Exception as e:
            self.logger.error(f"Error creating project with components: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to create project with components: {str(e)}")

    def add_component_to_project(self, project_id: int, component_id: int,
                                 quantity: int = 1) -> Dict[str, Any]:
        """Add a component to a project.

        Args:
            project_id: ID of the project
            component_id: ID of the component to add
            quantity: Quantity of the component

        Returns:
            Updated project with components

        Raises:
            EntityNotFoundError: If project or component not found
        """
        self.logger.debug(f"Adding component {component_id} to project {project_id}")
        from database.models.component import Component

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        component = self.session.query(Component).get(component_id)
        if not component:
            raise EntityNotFoundError(f"Component with ID {component_id} not found")

        try:
            # Check if component already exists in project
            existing = self.session.query(ProjectComponent). \
                filter(ProjectComponent.project_id == project_id). \
                filter(ProjectComponent.component_id == component_id).first()

            if existing:
                # Update quantity
                existing.quantity += quantity
                self.session.flush()
            else:
                # Create new project component
                project_component = ProjectComponent(
                    project_id=project_id,
                    component_id=component_id,
                    quantity=quantity
                )
                self.session.add(project_component)
                self.session.flush()

            # Return updated project with components
            return self.get_project_with_components(project_id)
        except Exception as e:
            self.logger.error(f"Error adding component to project: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to add component to project: {str(e)}")

    def update_component_quantity(self, project_id: int, project_component_id: int,
                                  quantity: int) -> Dict[str, Any]:
        """Update quantity of a component in a project.

        Args:
            project_id: ID of the project
            project_component_id: ID of the project component to update
            quantity: New quantity

        Returns:
            Updated project with components

        Raises:
            EntityNotFoundError: If project or project component not found
        """
        self.logger.debug(f"Updating component {project_component_id} quantity to {quantity}")

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        project_component = self.session.query(ProjectComponent).get(project_component_id)
        if not project_component or project_component.project_id != project_id:
            raise EntityNotFoundError(
                f"Project component with ID {project_component_id} not found in project {project_id}")

        try:
            # Update quantity
            project_component.quantity = quantity
            self.session.flush()

            # Return updated project with components
            return self.get_project_with_components(project_id)
        except Exception as e:
            self.logger.error(f"Error updating component quantity: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to update component quantity: {str(e)}")

    def remove_component_from_project(self, project_id: int, project_component_id: int) -> Dict[str, Any]:
        """Remove a component from a project.

        Args:
            project_id: ID of the project
            project_component_id: ID of the project component to remove

        Returns:
            Updated project with components

        Raises:
            EntityNotFoundError: If project or project component not found
        """
        self.logger.debug(f"Removing component {project_component_id} from project {project_id}")

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        project_component = self.session.query(ProjectComponent).get(project_component_id)
        if not project_component or project_component.project_id != project_id:
            raise EntityNotFoundError(
                f"Project component with ID {project_component_id} not found in project {project_id}")

        try:
            # Remove component
            self.session.delete(project_component)
            self.session.flush()

            # Return updated project with components
            return self.get_project_with_components(project_id)
        except Exception as e:
            self.logger.error(f"Error removing component from project: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to remove component from project: {str(e)}")

    # Status and scheduling methods

    def update_project_status(self, project_id: int,
                              status: ProjectStatus,
                              status_notes: Optional[str] = None) -> Dict[str, Any]:
        """Update project status with validation.

        Args:
            project_id: ID of the project
            status: New status
            status_notes: Optional notes about the status change

        Returns:
            Updated project data

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Updating project {project_id} status to {status.value}")

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        try:
            # Record status change in history
            from database.models.project_status_history import ProjectStatusHistory

            history = ProjectStatusHistory(
                project_id=project_id,
                old_status=project.status,
                new_status=status,
                change_date=datetime.now(),
                notes=status_notes
            )

            # Update project status
            project.status = status

            # If completing project, set end date
            if status == ProjectStatus.COMPLETED and not project.end_date:
                project.end_date = datetime.now()

            # Add notes if provided
            if status_notes and hasattr(project, 'notes'):
                if project.notes:
                    project.notes += f"\n[{datetime.now().isoformat()}] Status change: {status_notes}"
                else:
                    project.notes = f"[{datetime.now().isoformat()}] Status change: {status_notes}"

            # Save changes
            self.session.add(history)
            self.update(project)

            return project.to_dict()
        except Exception as e:
            self.logger.error(f"Error updating project status: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to update project status: {str(e)}")

    def reschedule_project(self, project_id: int,
                           new_start_date: Optional[datetime] = None,
                           new_end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Reschedule a project.

        Args:
            project_id: ID of the project
            new_start_date: New start date, or None to keep current
            new_end_date: New end date, or None to keep current

        Returns:
            Updated project data

        Raises:
            EntityNotFoundError: If project not found
            ValidationError: If dates are invalid
        """
        self.logger.debug(f"Rescheduling project {project_id}")

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        # Validate dates
        if new_start_date and new_end_date and new_start_date > new_end_date:
            raise ValidationError("Start date cannot be after end date")

        try:
            # Update dates
            if new_start_date:
                project.start_date = new_start_date

            if new_end_date:
                project.end_date = new_end_date

            # Save changes
            self.update(project)

            return project.to_dict()
        except Exception as e:
            self.logger.error(f"Error rescheduling project: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to reschedule project: {str(e)}")

    # Analytics and reporting methods

    def calculate_project_cost(self, project_id: int) -> Dict[str, Any]:
        """Calculate total project cost.

        Args:
            project_id: ID of the project

        Returns:
            Dict with cost breakdown

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Calculating costs for project {project_id}")
        from database.models.component import Component
        from database.models.component_material import ComponentMaterial
        from database.models.material import Material

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        # Get project components
        project_components = self.session.query(ProjectComponent). \
            filter(ProjectComponent.project_id == project_id).all()

        # Calculate material costs
        material_costs = 0
        material_details = []

        for pc in project_components:
            # Get component
            component = self.session.query(Component).get(pc.component_id)
            if not component:
                continue

            # Get component materials
            component_materials = self.session.query(ComponentMaterial). \
                filter(ComponentMaterial.component_id == component.id).all()

            for cm in component_materials:
                # Get material
                material = self.session.query(Material).get(cm.material_id)
                if not material:
                    continue

                # Calculate cost
                quantity_needed = cm.quantity * pc.quantity
                material_cost = quantity_needed * material.cost_per_unit if hasattr(material, 'cost_per_unit') else 0

                # Add to total
                material_costs += material_cost

                # Add details
                material_details.append({
                    'material_id': material.id,
                    'material_name': material.name,
                    'quantity_needed': quantity_needed,
                    'cost_per_unit': material.cost_per_unit if hasattr(material, 'cost_per_unit') else 0,
                    'total_cost': material_cost
                })

        # Estimate labor costs based on project type and complexity
        labor_rate = 25.0  # hourly rate
        estimated_hours = 0

        if project.type == ProjectType.WALLET:
            estimated_hours = 4
        elif project.type == ProjectType.BELT:
            estimated_hours = 3
        elif project.type == ProjectType.WATCH_STRAP:
            estimated_hours = 2
        elif project.type == ProjectType.BRIEFCASE:
            estimated_hours = 20
        elif project.type == ProjectType.MESSENGER_BAG:
            estimated_hours = 16
        else:
            estimated_hours = 8  # default

        labor_cost = labor_rate * estimated_hours

        # Overhead costs (example: 20% of materials + labor)
        overhead_cost = (material_costs + labor_cost) * 0.2

        # Total cost
        total_cost = material_costs + labor_cost + overhead_cost

        return {
            'project_id': project_id,
            'material_costs': material_costs,
            'material_details': material_details,
            'labor_cost': labor_cost,
            'labor_details': {
                'hourly_rate': labor_rate,
                'estimated_hours': estimated_hours
            },
            'overhead_cost': overhead_cost,
            'total_cost': total_cost,
            'calculated_at': datetime.now().isoformat()
        }

    def get_project_timeline_data(self, project_id: int) -> Dict[str, Any]:
        """Get timeline data for project.

        Args:
            project_id: ID of the project

        Returns:
            Dict with timeline data

        Raises:
            EntityNotFoundError: If project not found
        """
        self.logger.debug(f"Getting timeline data for project {project_id}")
        from database.models.project_status_history import ProjectStatusHistory

        project = self.get_by_id(project_id)
        if not project:
            raise EntityNotFoundError(f"Project with ID {project_id} not found")

        # Get status history
        status_history = self.session.query(ProjectStatusHistory). \
            filter(ProjectStatusHistory.project_id == project_id). \
            order_by(ProjectStatusHistory.change_date).all()

        # Get project components
        project_components = self.session.query(ProjectComponent). \
            filter(ProjectComponent.project_id == project_id).all()

        # Get related picking lists
        from database.models.picking_list import PickingList
        picking_lists = self.session.query(PickingList). \
            filter(PickingList.project_id == project_id).all()

        # Get related tool lists
        from database.models.tool_list import ToolList
        tool_lists = self.session.query(ToolList). \
            filter(ToolList.project_id == project_id).all()

        # Combine all timeline events
        timeline_events = []

        # Add project creation
        timeline_events.append({
            'event_type': 'PROJECT_CREATED',
            'date': project.created_at.isoformat() if hasattr(project, 'created_at') else None,
            'details': {
                'project_id': project.id,
                'name': project.name,
                'type': project.type.value
            }
        })

        # Add status changes
        for status_change in status_history:
            timeline_events.append({
                'event_type': 'STATUS_CHANGED',
                'date': status_change.change_date.isoformat() if status_change.change_date else None,
                'details': {
                    'old_status': status_change.old_status.value,
                    'new_status': status_change.new_status.value,
                    'notes': status_change.notes
                }
            })

        # Add picking list events
        for pl in picking_lists:
            timeline_events.append({
                'event_type': 'PICKING_LIST_CREATED',
                'date': pl.created_at.isoformat() if hasattr(pl, 'created_at') else None,
                'details': {
                    'picking_list_id': pl.id,
                    'status': pl.status.value
                }
            })

            if hasattr(pl, 'completed_at') and pl.completed_at:
                timeline_events.append({
                    'event_type': 'PICKING_LIST_COMPLETED',
                    'date': pl.completed_at.isoformat(),
                    'details': {
                        'picking_list_id': pl.id
                    }
                })

        # Add tool list events
        for tl in tool_lists:
            timeline_events.append({
                'event_type': 'TOOL_LIST_CREATED',
                'date': tl.created_at.isoformat() if hasattr(tl, 'created_at') else None,
                'details': {
                    'tool_list_id': tl.id,
                    'status': tl.status.value if hasattr(tl, 'status') else None
                }
            })

        # Sort events by date
        timeline_events.sort(key=lambda e: e['date'] if e['date'] else '0')

        return {
            'project': project.to_dict(),
            'timeline_events': timeline_events,
            'component_count': len(project_components),
            'picking_list_count': len(picking_lists),
            'tool_list_count': len(tool_lists)
        }

    # GUI-specific functionality

    def get_project_dashboard_data(self) -> Dict[str, Any]:
        """Get data for project dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting project dashboard data")

        # Get counts by status
        status_counts = self.count_projects_by_status()

        # Get active projects
        active_projects = self.get_active_projects()

        # Get overdue projects
        overdue_projects = self.get_overdue_projects()

        # Get projects completing soon (next 7 days)
        completing_soon_date = datetime.now() + timedelta(days=7)
        completing_soon = self.session.query(Project). \
            filter(Project.end_date <= completing_soon_date). \
            filter(Project.end_date >= datetime.now()). \
            filter(Project.status != ProjectStatus.COMPLETED). \
            filter(Project.status != ProjectStatus.CANCELLED).all()

        # Get recently completed projects (last 30 days)
        recent_completion_date = datetime.now() - timedelta(days=30)
        recently_completed = self.session.query(Project). \
            filter(Project.status == ProjectStatus.COMPLETED). \
            filter(Project.end_date >= recent_completion_date if hasattr(Project, 'end_date') else True).all()

        # Get counts by project type
        type_counts = self.session.query(
            Project.type,
            func.count().label('count')
        ).group_by(Project.type).all()

        type_data = {type_.value: count for type_, count in type_counts}

        # Combine all data
        return {
            'status_counts': status_counts,
            'type_counts': type_data,
            'active_count': len(active_projects),
            'overdue_count': len(overdue_projects),
            'completing_soon_count': len(completing_soon),
            'recently_completed_count': len(recently_completed),
            'active_projects': [p.to_dict() for p in active_projects[:5]],  # Top 5
            'overdue_projects': [p.to_dict() for p in overdue_projects[:5]],  # Top 5
            'completing_soon': [p.to_dict() for p in completing_soon[:5]],  # Top 5
            'recently_completed': [p.to_dict() for p in recently_completed[:5]]  # Top 5
        }

    def filter_projects_for_gui(self,
                                search_term: Optional[str] = None,
                                statuses: Optional[List[ProjectStatus]] = None,
                                project_types: Optional[List[ProjectType]] = None,
                                customer_id: Optional[int] = None,
                                start_date_from: Optional[datetime] = None,
                                start_date_to: Optional[datetime] = None,
                                end_date_from: Optional[datetime] = None,
                                end_date_to: Optional[datetime] = None,
                                sort_by: str = 'start_date',
                                sort_dir: str = 'desc',
                                page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate projects for GUI display.

        Args:
            search_term: Optional search term
            statuses: Optional list of statuses to filter by
            project_types: Optional list of project types to filter by
            customer_id: Optional customer ID to filter by
            start_date_from: Optional start date lower bound
            start_date_to: Optional start date upper bound
            end_date_from: Optional end date lower bound
            end_date_to: Optional end date upper bound
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(f"Filtering projects for GUI: statuses={statuses}, types={project_types}")
        from database.models.sales import Sales
        from database.models.customer import Customer

        # Build query
        query = self.session.query(Project)

        # Apply search filter if provided
        if search_term:
            query = query.filter(
                or_(
                    Project.name.ilike(f"%{search_term}%"),
                    Project.description.ilike(f"%{search_term}%") if hasattr(Project, 'description') else False
                )
            )

        # Apply status filter if provided
        if statuses:
            query = query.filter(Project.status.in_(statuses))

        # Apply type filter if provided
        if project_types:
            query = query.filter(Project.type.in_(project_types))

        # Apply customer filter if provided
        if customer_id:
            if hasattr(Project, 'customer_id'):
                query = query.filter(Project.customer_id == customer_id)
            elif hasattr(Project, 'sales_id'):
                query = query.join(Sales, Project.sales_id == Sales.id). \
                    filter(Sales.customer_id == customer_id)

        # Apply date filters if provided
        if start_date_from:
            query = query.filter(Project.start_date >= start_date_from)
        if start_date_to:
            query = query.filter(Project.start_date <= start_date_to)
        if end_date_from:
            query = query.filter(Project.end_date >= end_date_from)
        if end_date_to:
            query = query.filter(Project.end_date <= end_date_to)

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'name':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Project.name.desc())
            else:
                query = query.order_by(Project.name.asc())
        elif sort_by == 'status':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Project.status.desc())
            else:
                query = query.order_by(Project.status.asc())
        elif sort_by == 'type':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Project.type.desc())
            else:
                query = query.order_by(Project.type.asc())
        elif sort_by == 'start_date':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Project.start_date.desc())
            else:
                query = query.order_by(Project.start_date.asc())
        elif sort_by == 'end_date':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Project.end_date.desc())
            else:
                query = query.order_by(Project.end_date.asc())
        elif sort_by == 'created_at' and hasattr(Project, 'created_at'):
            if sort_dir.lower() == 'desc':
                query = query.order_by(Project.created_at.desc())
            else:
                query = query.order_by(Project.created_at.asc())
        else:
            # Default to start_date desc
            query = query.order_by(Project.start_date.desc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        projects = query.all()

        # Format results
        items = []
        for project in projects:
            project_dict = project.to_dict()

            # Add component count
            component_count = self.session.query(func.count()). \
                                  filter(ProjectComponent.project_id == project.id).scalar() or 0
            project_dict['component_count'] = component_count

            # Add customer info if available
            if hasattr(project, 'customer_id') and project.customer_id:
                customer = self.session.query(Customer).get(project.customer_id)
                if customer:
                    project_dict['customer'] = {
                        'id': customer.id,
                        'name': customer.name
                    }
            elif hasattr(project, 'sales_id') and project.sales_id:
                sales = self.session.query(Sales).get(project.sales_id)
                if sales and sales.customer_id:
                    customer = self.session.query(Customer).get(sales.customer_id)
                    if customer:
                        project_dict['customer'] = {
                            'id': customer.id,
                            'name': customer.name
                        }

            items.append(project_dict)

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }

    def export_project_data(self, project_id: Optional[int] = None,
                            format: str = "json") -> Dict[str, Any]:
        """Export project data to specified format.

        Args:
            project_id: Optional ID of specific project to export, or None for all
            format: Export format ("json" or "csv")

        Returns:
            Dict with export data and metadata

        Raises:
            EntityNotFoundError: If specific project not found
        """
        self.logger.debug(f"Exporting project data in {format} format")

        if project_id:
            # Export specific project with details
            project = self.get_by_id(project_id)
            if not project:
                raise EntityNotFoundError(f"Project with ID {project_id} not found")

            # Get full project data with components
            project_data = self.get_project_with_components(project_id)

            # Get cost information
            cost_data = self.calculate_project_cost(project_id)

            # Get timeline
            timeline_data = self.get_project_timeline_data(project_id)

            # Combine data
            export_data = {
                'project': project_data,
                'costs': cost_data,
                'timeline': timeline_data
            }

            # Create metadata
            metadata = {
                'count': 1,
                'timestamp': datetime.now().isoformat(),
                'format': format,
                'project_id': project_id,
                'project_name': project.name
            }
        else:
            # Export all projects (basic info only)
            projects = self.get_all(limit=1000)  # Reasonable limit

            # Transform to dictionaries
            export_data = [p.to_dict() for p in projects]

            # Create metadata
            metadata = {
                'count': len(export_data),
                'timestamp': datetime.now().isoformat(),
                'format': format,
                'status_counts': {
                    status.value: len([p for p in projects if p.status == status])
                    for status in ProjectStatus
                }
            }

        return {
            'data': export_data,
            'metadata': metadata
        }