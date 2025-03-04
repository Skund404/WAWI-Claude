# database/models/components.py
"""
Component models for patterns and projects.
"""

from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
from typing import Optional

from database.models.base import Base
from database.models.enums import ComponentType, MaterialType
from utils.circular_import_resolver import lazy_import, register_lazy_import

# Register lazy imports to avoid circular dependencies
register_lazy_import('database.models.project.Project', 'database.models.project')
register_lazy_import('database.models.pattern.Pattern', 'database.models.pattern')
register_lazy_import('database.models.material.Material', 'database.models.material')
register_lazy_import('database.models.leather.Leather', 'database.models.leather')
register_lazy_import('database.models.hardware.Hardware', 'database.models.hardware')


class Component(Base):
    """
    Base model for all component types.
    """
    __abstract__ = True  # Mark as abstract to prevent direct table creation

    # Common fields for all components
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Float, default=1.0, nullable=False)

    # Component metadata
    width = Column(Float, nullable=True)  # in inches or cm
    height = Column(Float, nullable=True)  # in inches or cm
    length = Column(Float, nullable=True)  # in inches or cm
    area = Column(Float, nullable=True)  # calculated area
    notes = Column(Text, nullable=True)

    # Single-table inheritance discriminator
    type = Column(String(50), nullable=False)

    __mapper_args__ = {
        'polymorphic_on': type
    }

    def calculate_area(self) -> Optional[float]:
        """
        Calculate the area of the component if dimensions are provided.

        Returns:
            Optional[float]: Calculated area or None if dimensions are missing
        """
        if self.width and self.height:
            self.area = self.width * self.height
            return self.area
        return None


class ProjectComponent(Component):
    """
    Components used in specific projects.
    """
    __tablename__ = 'components'

    # Additional fields specific to project components
    is_complete = Column(Boolean, default=False, nullable=False)

    # Material relationship fields
    material_type = Column(Enum(MaterialType), nullable=True)

    # Foreign keys for different material types
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    leather_id = Column(Integer, ForeignKey("leathers.id"), nullable=True)
    hardware_id = Column(Integer, ForeignKey("hardwares.id"), nullable=True)

    # Project foreign key
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)

    # Relationships with explicit join conditions
    project = relationship(
        "Project",
        primaryjoin="ProjectComponent.project_id == Project.id",
        foreign_keys=[project_id],
        back_populates="components"
    )

    # Generic material relationship
    material = relationship(
        "Material",
        primaryjoin="ProjectComponent.material_id == Material.id",
        foreign_keys=[material_id],
        viewonly=False
    )

    # Leather relationship
    leather = relationship(
        "Leather",
        primaryjoin="ProjectComponent.leather_id == Leather.id",
        foreign_keys=[leather_id],
        viewonly=False
    )

    # Hardware relationship
    hardware = relationship(
        "Hardware",
        primaryjoin="ProjectComponent.hardware_id == Hardware.id",
        foreign_keys=[hardware_id],
        viewonly=False
    )

    __mapper_args__ = {
        'polymorphic_identity': 'project_component'
    }

    def __init__(self, **kwargs):
        """
        Initialize a project component with validation.

        Args:
            **kwargs: Component attributes

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        if 'project_id' not in kwargs:
            raise ValueError("Project ID is required for project components")

        if 'name' not in kwargs:
            raise ValueError("Component name is required")

        # Validate material relationships
        material_fields = sum(1 for field in ['material_id', 'leather_id', 'hardware_id']
                              if field in kwargs and kwargs[field] is not None)

        if material_fields > 1:
            raise ValueError("Only one material type can be associated with a component")

        # Set material_type based on the provided material ID
        if 'leather_id' in kwargs and kwargs['leather_id'] is not None:
            kwargs['material_type'] = MaterialType.LEATHER
        elif 'hardware_id' in kwargs and kwargs['hardware_id'] is not None:
            kwargs['material_type'] = MaterialType.HARDWARE
        elif 'material_id' in kwargs and kwargs['material_id'] is not None:
            kwargs['material_type'] = MaterialType.GENERIC

        super().__init__(**kwargs)

    def mark_complete(self, is_complete: bool = True) -> None:
        """
        Mark the component as complete or incomplete.

        Args:
            is_complete (bool): Component completion status
        """
        self.is_complete = is_complete

    def calculate_cost(self) -> Optional[float]:
        """
        Calculate the cost of this component based on material and dimensions.

        Returns:
            Optional[float]: Component cost or None if cannot be calculated
        """
        # Ensure area is calculated
        if not self.area:
            self.calculate_area()

        if not self.area:
            return None

        # Calculate cost based on material type
        if self.material_type == MaterialType.LEATHER and self.leather:
            return self.area * self.leather.cost_per_sqft * self.quantity
        elif self.material_type == MaterialType.HARDWARE and self.hardware:
            return self.hardware.cost_per_unit * self.quantity
        elif self.material_type == MaterialType.GENERIC and self.material:
            # This would need to be implemented based on your material pricing model
            return None

        return None

    def __repr__(self) -> str:
        """String representation of the component."""
        return f"<ProjectComponent(id={self.id}, name='{self.name}', project_id={self.project_id})>"


class PatternComponent(Component):
    """
    Components used in pattern templates.
    """
    __tablename__ = 'pattern_components'

    # Pattern component specific fields
    suggested_material = Column(String(255), nullable=True)
    instructions = Column(Text, nullable=True)

    # Pattern foreign key
    pattern_id = Column(Integer, ForeignKey("patterns.id"), nullable=False)

    # Relationships with explicit join conditions
    pattern = relationship(
        "Pattern",
        primaryjoin="PatternComponent.pattern_id == Pattern.id",
        foreign_keys=[pattern_id],
        back_populates="components"
    )

    __mapper_args__ = {
        'polymorphic_identity': 'pattern_component'
    }

    def __init__(self, **kwargs):
        """
        Initialize a pattern component with validation.

        Args:
            **kwargs: Component attributes

        Raises:
            ValueError: If validation fails
        """
        # Validate required fields
        if 'pattern_id' not in kwargs:
            raise ValueError("Pattern ID is required for pattern components")

        if 'name' not in kwargs:
            raise ValueError("Component name is required")

        super().__init__(**kwargs)

    def create_project_component(self, project_id: int, **kwargs) -> ProjectComponent:
        """
        Create a project component based on this pattern component.

        Args:
            project_id (int): ID of the project to associate with
            **kwargs: Additional attributes for the project component

        Returns:
            ProjectComponent: Newly created project component
        """
        # Combine pattern component attributes with provided kwargs
        component_data = {
            'name': self.name,
            'description': self.description,
            'width': self.width,
            'height': self.height,
            'length': self.length,
            'quantity': self.quantity,
            'project_id': project_id,
            'area': self.area
        }

        # Override with any provided kwargs
        component_data.update(kwargs)

        # Create and return the new project component
        return ProjectComponent(**component_data)

    def __repr__(self) -> str:
        """String representation of the component."""
        return f"<PatternComponent(id={self.id}, name='{self.name}', pattern_id={self.pattern_id})>"