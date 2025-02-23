# database/models/interfaces.py

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime


class IComponent(ABC):
    """Base interface for all components."""

    @abstractmethod
    def calculate_cost(self) -> float:
        """Calculate the cost of this component."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate the component's data."""
        pass

    @abstractmethod
    def get_material_requirements(self) -> Dict[str, float]:
        """Get the material requirements for this component."""
        pass


class IProject(ABC):
    """Base interface for projects."""

    @abstractmethod
    def calculate_complexity(self) -> float:
        """Calculate the complexity score of the project."""
        pass

    @abstractmethod
    def calculate_total_cost(self) -> float:
        """Calculate the total cost of the project."""
        pass

    @abstractmethod
    def get_status(self) -> str:
        """Get the current status of the project."""
        pass

    @abstractmethod
    def update_status(self, new_status: str) -> None:
        """Update the project status."""
        pass


class IRecipe(ABC):
    """Base interface for recipes."""

    @abstractmethod
    def calculate_total_cost(self) -> float:
        """Calculate the total cost of the recipe."""
        pass

    @abstractmethod
    def check_material_availability(self) -> bool:
        """Check if all required materials are available."""
        pass

    @abstractmethod
    def generate_material_list(self) -> Dict[str, float]:
        """Generate a list of required materials."""
        pass


# database/models/mixins.py

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, DateTime, String


class TimestampMixin:
    """Mixin to add timestamp functionality to models."""

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def update_timestamp(self) -> None:
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()


class NoteMixin:
    """Mixin to add notes functionality to models."""

    notes = Column(String(1000))

    def add_note(self, note: str) -> None:
        """Add a note to the existing notes."""
        if self.notes:
            self.notes = f"{self.notes}\n{note}"
        else:
            self.notes = note


class CostingMixin:
    """Mixin to add costing functionality to models."""

    def calculate_labor_cost(self, hours: float, rate: float) -> float:
        """Calculate labor cost."""
        return hours * rate

    def calculate_overhead_cost(self, base_cost: float, overhead_rate: float) -> float:
        """Calculate overhead cost."""
        return base_cost * overhead_rate

    def calculate_total_cost(self, material_cost: float, labor_cost: float, overhead_rate: float = 0.1) -> float:
        """Calculate total cost including overhead."""
        base_cost = material_cost + labor_cost
        overhead_cost = self.calculate_overhead_cost(base_cost, overhead_rate)
        return base_cost + overhead_cost


class ValidationMixin:
    """Mixin to add validation functionality to models."""

    def validate_required_fields(self, required_fields: List[str]) -> bool:
        """Validate that all required fields have values."""
        return all(hasattr(self, field) and getattr(self, field) is not None
                   for field in required_fields)

    def validate_numeric_range(self, value: float, min_val: float, max_val: float) -> bool:
        """Validate that a numeric value is within the specified range."""
        return min_val <= value <= max_val