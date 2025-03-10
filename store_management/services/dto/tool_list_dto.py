# services/dto/tool_list_dto.py
# Data Transfer Object for Tool List

from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict


@dataclass
class ToolListItemDTO:
    """Data Transfer Object for Tool List Item."""

    id: int
    tool_list_id: int
    tool_id: int
    quantity: int
    tool_name: Optional[str] = None
    tool_type: Optional[str] = None
    available: Optional[bool] = None
    storage_location: Optional[str] = None

    @classmethod
    def from_model(cls, model):
        """Create DTO from model instance.

        Args:
            model: ToolListItem model instance

        Returns:
            ToolListItemDTO instance
        """
        dto = cls(
            id=model.id,
            tool_list_id=model.tool_list_id,
            tool_id=model.tool_id,
            quantity=model.quantity
        )

        # Add tool information if available
        if hasattr(model, 'tool') and model.tool:
            dto.tool_name = model.tool.name
            dto.tool_type = model.tool.tool_type if hasattr(model.tool, 'tool_type') else None

            # Add availability and storage location if available from inventory
            if hasattr(model.tool, 'inventory') and model.tool.inventory:
                dto.available = model.tool.inventory.status != 'OUT_OF_STOCK'
                dto.storage_location = model.tool.inventory.storage_location

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ToolListDTO:
    """Data Transfer Object for Tool List."""

    id: int
    project_id: int
    status: str
    created_at: datetime
    project_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None
    items: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_model(cls, model, include_items=False, include_project=False):
        """Create DTO from model instance.

        Args:
            model: ToolList model instance
            include_items: Whether to include tool list items
            include_project: Whether to include project information

        Returns:
            ToolListDTO instance
        """
        dto = cls(
            id=model.id,
            project_id=model.project_id,
            status=model.status,
            created_at=model.created_at,
            completed_at=model.completed_at if hasattr(model, 'completed_at') and model.completed_at else None,
            notes=model.notes if hasattr(model, 'notes') else None
        )

        # Add items if requested and available
        if include_items and hasattr(model, 'items') and model.items:
            dto.items = [ToolListItemDTO.from_model(item).to_dict() for item in model.items]

        # Add project information if requested and available
        if include_project and hasattr(model, 'project') and model.project:
            dto.project_name = model.project.name

        return dto

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation of the DTO
        """
        return {k: v for k, v in asdict(self).items() if v is not None}