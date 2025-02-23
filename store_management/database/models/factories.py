# database/models/factories.py

from typing import Optional, Dict, Any
from .project import Project
from .pattern import Recipe
from .components import ProjectComponent, RecipeComponent
from .enums import ProjectType, ProjectStatus, SkillLevel, ComponentType, MaterialType


class ProjectFactory:
    """Factory for creating projects and project components."""

    @staticmethod
    def create_project(
            name: str,
            project_type: ProjectType,
            skill_level: SkillLevel,
            description: Optional[str] = None,
            estimated_hours: Optional[float] = None
    ) -> Project:
        """Create a new project with basic configuration."""
        project = Project(
            name=name,
            project_type=project_type,
            skill_level=skill_level,
            description=description,
            estimated_hours=estimated_hours,
            status=ProjectStatus.PLANNED
        )
        return project

    @staticmethod
    def create_project_component(
            name: str,
            material_type: MaterialType,
            quantity: float,
            unit_cost: float,
            component_type: ComponentType = ComponentType.STRUCTURAL,
            description: Optional[str] = None
    ) -> ProjectComponent:
        """Create a new project component."""
        component = ProjectComponent(
            name=name,
            material_type=material_type,
            quantity=quantity,
            unit_cost=unit_cost,
            component_type=component_type,
            description=description,
            actual_quantity=0.0,
            wastage=0.0
        )
        return component


class RecipeFactory:
    """Factory for creating recipes and recipe components."""

    @staticmethod
    def create_recipe(
            name: str,
            base_labor_hours: float,
            description: Optional[str] = None,
            is_template: bool = False,
            version: Optional[str] = None,
            difficulty_multiplier: float = 1.0
    ) -> Recipe:
        """Create a new recipe with basic configuration."""
        recipe = Recipe(
            name=name,
            base_labor_hours=base_labor_hours,
            description=description,
            is_template=is_template,
            version=version or "1.0",
            difficulty_multiplier=difficulty_multiplier
        )
        return recipe

    @staticmethod
    def create_recipe_component(
            name: str,
            material_type: MaterialType,
            quantity: float,
            unit_cost: float,
            minimum_quantity: Optional[float] = None,
            substitutable: bool = False,
            component_type: ComponentType = ComponentType.STRUCTURAL,
            description: Optional[str] = None
    ) -> RecipeComponent:
        """Create a new recipe component."""
        component = RecipeComponent(
            name=name,
            material_type=material_type,
            quantity=quantity,
            unit_cost=unit_cost,
            component_type=component_type,
            description=description,
            minimum_quantity=minimum_quantity or quantity,
            substitutable=substitutable
        )
        return component