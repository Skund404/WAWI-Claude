# database/models/__init__.py

from .enums import (
    ProjectType, ProjectStatus, SkillLevel, MaterialType,
    LeatherType, MaterialQualityGrade, ComponentType,
    InventoryStatus, TransactionType, MeasurementUnit
)
from .interfaces import IComponent, IProject, IRecipe
from .mixins import TimestampMixin, NoteMixin, CostingMixin, ValidationMixin
from .components import Component, ProjectComponent, RecipeComponent
from .project import Project
from .pattern import Pattern
from .factories import ProjectFactory, RecipeFactory
from .config import ModelConfiguration, MaterialConfig, ComponentConfig

__all__ = [
    # Enums
    'ProjectType', 'ProjectStatus', 'SkillLevel', 'MaterialType',
    'LeatherType', 'MaterialQualityGrade', 'ComponentType',
    'InventoryStatus', 'TransactionType', 'MeasurementUnit',

    # Interfaces
    'IComponent', 'IProject', 'IRecipe',

    # Mixins
    'TimestampMixin', 'NoteMixin', 'CostingMixin', 'ValidationMixin',

    # Models
    'Component', 'ProjectComponent', 'RecipeComponent',
    'Project', 'Pattern',

    # Factories
    'ProjectFactory', 'RecipeFactory',

    # Configuration
    'ModelConfiguration', 'MaterialConfig', 'ComponentConfig'
]

# Initialize default configurations
ModelConfiguration.initialize_default_configs()