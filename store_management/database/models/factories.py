

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService


class ProjectFactory:
    """
    Factory class for creating Project and related objects.
    """

    @staticmethod
    def create_project(name: str, project_type: ProjectType = ProjectType.
                       LEATHER_GOODS, skill_level: SkillLevel = SkillLevel.BEGINNER,
                       description: Optional[str] = None, estimated_hours: float = 0.0) -> Project:
        """
        Create a new Project instance with the specified attributes.

        Args:
            name: Project name
            project_type: Type of project (default: LEATHER_GOODS)
            skill_level: Required skill level (default: BEGINNER)
            description: Project description (optional)
            estimated_hours: Estimated hours for completion

        Returns:
            Project: New Project instance
        """
        project = Project()
        project.name = name
        project.project_type = project_type
        project.skill_level = skill_level
        project.description = description
        project.estimated_hours = estimated_hours
        project.created_at = datetime.now()
        project.updated_at = datetime.now()
        return project

        @staticmethod
    def create_project_component(name: str, material_type: MaterialType,
                                 quantity: float, unit_cost: float, component_type: ComponentType,
                                 description: Optional[str] = None) -> ProjectComponent:
        """
        Create a new ProjectComponent instance.

        Args:
            name: Component name
            material_type: Type of material required
            quantity: Quantity needed
            unit_cost: Cost per unit
            component_type: Type of component
            description: Component description (optional)

        Returns:
            ProjectComponent: New ProjectComponent instance
        """
        component = ProjectComponent()
        component.name = name
        component.material_type = material_type
        component.quantity = quantity
        component.unit_cost = unit_cost
        component.component_type = component_type
        component.description = description
        component.created_at = datetime.now()
        component.updated_at = datetime.now()
        return component


class PatternFactory:
    """
    Factory class for creating Pattern and related objects.
    """

    @staticmethod
    def create_pattern(name: str, base_labor_hours: float, description:
                       Optional[str] = None, is_template: bool = False, version: str = '1.0',
                       difficulty_multiplier: float = 1.0) -> Pattern:
        """
        Create a new Pattern instance.

        Args:
            name: Pattern name
            base_labor_hours: Base time required for completion
            description: Pattern description (optional)
            is_template: Whether this is a template pattern
            version: Pattern version
            difficulty_multiplier: Multiplier for difficulty calculation

        Returns:
            Pattern: New Pattern instance
        """
        pattern = Pattern()
        pattern.name = name
        pattern.base_labor_hours = base_labor_hours
        pattern.description = description
        pattern.is_template = is_template
        pattern.version = version
        pattern.difficulty_multiplier = difficulty_multiplier
        pattern.created_at = datetime.now()
        pattern.updated_at = datetime.now()
        return pattern

        @staticmethod
    def create_pattern_component(name: str, material_type: MaterialType,
                                 quantity: float, unit_cost: float, minimum_quantity: float = 0.0,
                                 substitutable: bool = False, component_type: ComponentType =
                                 ComponentType.MAIN_BODY, description: Optional[str] = None,
                                 stitch_type: Optional[StitchType] = None, edge_finish_type: Optional[
                                     EdgeFinishType] = None) -> PatternComponent:
        """
        Create a new PatternComponent instance.

        Args:
            name: Component name
            material_type: Type of material required
            quantity: Quantity needed
            unit_cost: Cost per unit
            minimum_quantity: Minimum quantity required
            substitutable: Whether material can be substituted
            component_type: Type of component
            description: Component description (optional)
            stitch_type: Type of stitching required (optional)
            edge_finish_type: Type of edge finishing required (optional)

        Returns:
            PatternComponent: New PatternComponent instance
        """
        component = PatternComponent()
        component.name = name
        component.material_type = material_type
        component.quantity = quantity
        component.unit_cost = unit_cost
        component.minimum_quantity = minimum_quantity
        component.substitutable = substitutable
        component.component_type = component_type
        component.description = description
        component.stitch_type = stitch_type
        component.edge_finish_type = edge_finish_type
        component.created_at = datetime.now()
        component.updated_at = datetime.now()
        return component
