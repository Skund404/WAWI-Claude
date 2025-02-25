# database/models/pattern.py
"""
Pattern model module for the leatherworking store management system.

Defines the Pattern class for tracking leatherworking patterns.
"""

import datetime
from typing import Dict, Any, List, Optional

from sqlalchemy import (
    Column, String, Integer, Float, ForeignKey, Boolean,
    DateTime, Text, Table
)
from sqlalchemy.orm import relationship

from database.models.base import Base, BaseModel

# Association table for pattern-component relationship
pattern_components = Table(
    'pattern_components',
    Base.metadata,
    Column('pattern_id', Integer, ForeignKey('pattern.id'), primary_key=True),
    Column('component_id', Integer, ForeignKey('project_component.id'), primary_key=True)
)


class Pattern(Base, BaseModel):
    """
    Model for leatherworking patterns.

    A pattern represents the template for creating a leatherwork project,
    including the components, measurements, and assembly instructions.
    """
    __tablename__ = 'pattern'

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(20), nullable=True)
    difficulty = Column(Integer, default=1)  # Scale 1-5
    estimated_time = Column(Float, nullable=True)  # In hours

    # Design information
    dimensions = Column(String(100), nullable=True)  # eg. "10in x 6in x 2in"
    image_path = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)

    # Digital file information
    file_path = Column(String(255), nullable=True)
    file_format = Column(String(50), nullable=True)

    # Permissions and sharing
    is_public = Column(Boolean, default=False)
    author = Column(String(100), nullable=True)

    # Relationships
    components = relationship("ProjectComponent", secondary=pattern_components)
    projects = relationship("Project", back_populates="pattern")

    def __repr__(self) -> str:
        """
        Return a string representation of the pattern.

        Returns:
            str: String representation with id and name
        """
        return f"<Pattern id={self.id}, name='{self.name}'>"

    def calculate_total_material(self) -> Dict[str, float]:
        """
        Calculate the total material requirements for this pattern.

        Returns:
            Dict[str, float]: Material requirements by type
        """
        requirements = {}
        for component in self.components:
            material_type = None

            if component.material:
                material_type = component.material.material_type.name
            elif component.leather:
                material_type = f"Leather-{component.leather.leather_type.name}"
            elif component.part:
                material_type = f"Part-{component.part.name}"

            if material_type:
                if material_type not in requirements:
                    requirements[material_type] = 0
                requirements[material_type] += component.quantity

        return requirements

    def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of materials for this pattern.

        Returns:
            float: Total cost of all components
        """
        total_cost = 0.0
        for component in self.components:
            total_cost += (component.unit_cost * component.quantity)
        return total_cost

    def check_material_availability(self) -> Dict[str, Any]:
        """
        Check if all required materials are available in sufficient quantities.

        Returns:
            Dict[str, Any]: Availability status for each component
        """
        result = {
            "available": True,
            "components": []
        }

        for component in self.components:
            component_data = {
                "name": component.name,
                "quantity_needed": component.quantity,
                "available": False,
                "available_quantity": 0
            }

            # Check material availability
            if component.material:
                component_data["available_quantity"] = component.material.current_stock
                component_data["available"] = component.material.current_stock >= component.quantity
            elif component.leather:
                component_data["available_quantity"] = component.leather.current_area
                component_data["available"] = component.leather.current_area >= component.quantity
            elif component.part:
                component_data["available_quantity"] = component.part.current_quantity
                component_data["available"] = component.part.current_quantity >= component.quantity

            if not component_data["available"]:
                result["available"] = False

            result["components"].append(component_data)

        return result