# services/dto/project_dto.py
# Data Transfer Object for Project

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class ProjectComponentDTO:
    """Data Transfer Object for Project Component."""

    id: int
    project_id: int
    component_id: int
    quantity: float
    component_name: Optional[str] = None
    component_type: Optional[str] = None
    notes: Optional[str] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: ProjectComponent model instance

        Returns:
            ProjectComponentDTO instance
        """
        dto = cls(
            id=model.id,
            project_id=model.project_id,
            component_id=model.component_id,
            quantity=model.quantity,
            notes=model.notes if hasattr(model, 'notes') else None
        )

        # Add component information if available
        if hasattr(model, 'component') and model.component:
            dto.component_name = model.component.name
            dto.component_type = model.component.component_type

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProjectDTO:
    """Data Transfer Object for Project."""

    id: int
    name: str
    type: str
    status: str
    start_date: datetime
    description: Optional[str] = None
    end_date: Optional[datetime] = None
    sales_id: Optional[int] = None
    customer_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    components: List[Dict[str, Any]] = field(default_factory=list)
    estimated_cost: Optional[float] = None
    actual_cost: Optional[float] = None
    customer_name: Optional[str] = None

    @classmethod
    def from_model(cls, model, include_components=False, include_customer=False):
        """Create DTO from model instance.

        Args:
            model: Project model instance
            include_components: Whether to include project components
            include_customer: Whether to include customer information

        Returns:
            ProjectDTO instance
        """
        dto = cls(
            id=model.id,
            name=model.name,
            type=model.type,
            status=model.status,
            start_date=model.start_date,
            description=model.description if hasattr(model, 'description') else None,
            end_date=model.end_date if hasattr(model, 'end_date') and model.end_date else None,
            sales_id=model.sales_id if hasattr(model, 'sales_id') else None,
            customer_id=model.customer_id if hasattr(model, 'customer_id') else None,
            created_at=model.created_at if hasattr(model, 'created_at') else None,
            updated_at=model.updated_at if hasattr(model, 'updated_at') else None,
            estimated_cost=model.estimated_cost if hasattr(model, 'estimated_cost') else None,
            actual_cost=model.actual_cost if hasattr(model, 'actual_cost') else None
        )

        # Add components if requested and available
        if include_components and hasattr(model, 'components') and model.components:
            dto.components = [ProjectComponentDTO.from_model(pc).to_dict() for pc in model.components]

        # Add customer information if requested and available
        if include_customer and hasattr(model, 'customer') and model.customer:
            dto.customer_name = model.customer.name
        elif include_customer and hasattr(model, 'sales') and model.sales and hasattr(model.sales,
                                                                                      'customer') and model.sales.customer:
            dto.customer_name = model.sales.customer.name

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProjectStatusHistoryDTO:
    """Data Transfer Object for Project Status History."""

    id: int
    project_id: int
    status: str
    timestamp: datetime
    notes: Optional[str] = None
    user_id: Optional[int] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: ProjectStatusHistory model instance

        Returns:
            ProjectStatusHistoryDTO instance
        """
        return cls(
            id=model.id,
            project_id=model.project_id,
            status=model.status,
            timestamp=model.timestamp,
            notes=model.notes if hasattr(model, 'notes') else None,
            user_id=model.user_id if hasattr(model, 'user_id') else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}