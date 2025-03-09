# database/models/project_component.py
from typing import Any, Dict, List, Optional

from sqlalchemy import Column, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.models.base import AbstractBase, ModelValidationError, ValidationMixin


class ProjectComponent(AbstractBase, ValidationMixin):
    """
    Junction table between Project and Component with additional attributes.

    Attributes:
        project_id (int): Foreign key to the project
        component_id (int): Foreign key to the component
        quantity (float): Quantity of component needed for the project
    """
    __tablename__ = 'project_components'
    __table_args__ = {'extend_existing': True}

    # We'll use regular primary key here to avoid issues with composite keys
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    component_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("components.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=1.0
    )

    # Relationships
    project = relationship(
        "Project",
        back_populates="project_components",
        lazy="selectin"
    )

    component = relationship(
        "Component",
        lazy="selectin"
    )

    def __init__(self, **kwargs):
        """
        Initialize a ProjectComponent instance with validation.
        """
        super().__init__(**kwargs)
        self.validate()

    def validate(self) -> None:
        """
        Validate project component data.

        Raises:
            ModelValidationError: If validation fails
        """
        # Project ID validation
        if not self.project_id or not isinstance(self.project_id, int):
            raise ModelValidationError("Project ID must be a positive integer")

        if self.project_id <= 0:
            raise ModelValidationError("Project ID must be a positive integer")

        # Component ID validation
        if not self.component_id or not isinstance(self.component_id, int):
            raise ModelValidationError("Component ID must be a positive integer")

        if self.component_id <= 0:
            raise ModelValidationError("Component ID must be a positive integer")

        # Quantity validation
        if not self.quantity or not isinstance(self.quantity, (int, float)):
            raise ModelValidationError("Quantity must be a positive number")

        if self.quantity <= 0:
            raise ModelValidationError("Quantity must be a positive number")

        return self