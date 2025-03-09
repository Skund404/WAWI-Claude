# database/models/project_component.py
from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from database.models.base import AbstractBase, ValidationMixin, ModelValidationError


class ProjectComponent(AbstractBase, ValidationMixin):
    """
    ProjectComponent represents the relationship between a project and its required components.

    Attributes:
        project_id: Foreign key to the project
        component_id: Foreign key to the component
        quantity: Number of components needed
        completed_quantity: Number of components completed
    """
    __tablename__ = 'project_components'

    project_id: Mapped[int] = mapped_column(Integer, ForeignKey('projects.id'), nullable=False)
    component_id: Mapped[int] = mapped_column(Integer, ForeignKey('components.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Relationships
    project = relationship("Project", back_populates="components")
    component = relationship("Component", back_populates="project_components")

    def __init__(self, **kwargs):
        """Initialize a ProjectComponent instance with validation."""
        super().__init__(**kwargs)
        self.validate()

    def validate(self):
        """Validate project component data."""
        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be positive")

        if self.completed_quantity < 0:
            raise ModelValidationError("Completed quantity cannot be negative")

        if self.completed_quantity > self.quantity:
            raise ModelValidationError("Completed quantity cannot exceed quantity")

    def update_completion(self, amount: int) -> None:
        """
        Update completion status.

        Args:
            amount: Amount to add to completed_quantity
        """
        if amount <= 0:
            raise ValueError("Completion amount must be positive")

        if self.completed_quantity + amount > self.quantity:
            raise ValueError("Cannot complete more than the total quantity")

        self.completed_quantity += amount