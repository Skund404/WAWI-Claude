# database/models/factories.py

from typing import Optional, Dict, Any
from ..models.project import Project
from ..models.pattern import Pattern
from ..models.components import ProjectComponent, RecipeComponent
from ..models.enums import (
    ProjectType,
    ProjectStatus,
    SkillLevel,
    ComponentType,
    MaterialType
)

class ProjectFactory:
    """
    Factory for creating projects and project components.
    Provides standardized way to instantiate project-related objects.
    """

    @staticmethod
    def create_project(
        name: str,
        project_type: ProjectType = ProjectType.LEATHER_GOODS,
        skill_level: SkillLevel = SkillLevel.INTERMEDIATE,
        description: Optional[str] = None,
        estimated_hours: float = 0.0
    ) -> Project:
        """
        Create a new project with basic configuration.

        Args:
            name: Name of the project
            project_type: Type of leatherworking project
            skill_level: Required skill level
            description: Optional project description
            estimated_hours: Estimated hours to complete

        Returns:
            Project: Newly created project instance
        """
        return Project(
            name=name,
            project_type=project_type,
            skill_level=skill_level,
            description=description,
            estimated_hours=estimated_hours,
            status=ProjectStatus.NEW
        )

    @staticmethod
    def create_project_component(
        name: str,
        material_type: MaterialType,
        quantity: float,
        unit_cost: float,
        component_type: ComponentType = ComponentType.MAIN,
        description: Optional[str] = None
    ) -> ProjectComponent:
        """
        Create a new project component.

        Args:
            name: Component name
            material_type: Type of material used
            quantity: Quantity needed
            unit_cost: Cost per unit
            component_type: Type of component
            description: Optional component description

        Returns:
            ProjectComponent: Newly created component instance
        """
        component = ProjectComponent(
            name=name,
            material_type=material_type,
            quantity=quantity,
            unit_cost=unit_cost,
            component_type=component_type,
            description=description
        )
        return component


class RecipeFactory:
    """
    Factory for creating recipes and recipe components.
    Provides standardized way to instantiate recipe-related objects.
    """

    @staticmethod
    def create_recipe(
        name: str,
        base_labor_hours: float,
        description: Optional[str] = None,
        is_template: bool = False,
        version: str = "1.0",
        difficulty_multiplier: float = 1.0
    ) -> Recipe:
        """
        Create a new recipe with basic configuration.

        Args:
            name: Recipe name
            base_labor_hours: Base labor hours required
            description: Optional recipe description
            is_template: Whether this is a template recipe
            version: Recipe version
            difficulty_multiplier: Multiplier for difficulty calculations

        Returns:
            Recipe: Newly created recipe instance
        """
        return Recipe(
            name=name,
            base_labor_hours=base_labor_hours,
            description=description,
            is_template=is_template,
            version=version,
            difficulty_multiplier=difficulty_multiplier
        )

    @staticmethod
    def create_recipe_component(
        name: str,
        material_type: MaterialType,
        quantity: float,
        unit_cost: float,
        minimum_quantity: Optional[float] = None,
        substitutable: bool = False,
        component_type: ComponentType = ComponentType.MAIN,
        description: Optional[str] = None
    ) -> RecipeComponent:
        """
        Create a new recipe component.

        Args:
            name: Component name
            material_type: Type of material used
            quantity: Quantity needed
            unit_cost: Cost per unit
            minimum_quantity: Minimum required quantity
            substitutable: Whether material can be substituted
            component_type: Type of component
            description: Optional component description

        Returns:
            RecipeComponent: Newly created component instance
        """
        component = RecipeComponent(
            name=name,
            material_type=material_type,
            quantity=quantity,
            unit_cost=unit_cost,
            minimum_quantity=minimum_quantity,
            substitutable=substitutable,
            component_type=component_type,
            description=description
        )
        return component