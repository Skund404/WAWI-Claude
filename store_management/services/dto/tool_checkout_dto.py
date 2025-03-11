# services/dto/tool_checkout_dto.py
"""
Data Transfer Object for tool checkout records.

This module defines the DTO for transferring tool checkout data
between the service layer and the UI.
"""

import dataclasses
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ToolCheckoutDTO:
    """Data Transfer Object for Tool Checkout."""

    id: int
    tool_id: int
    checked_out_by: str
    checked_out_date: datetime
    due_date: Optional[datetime] = None
    returned_date: Optional[datetime] = None
    status: str = "checked_out"
    notes: Optional[str] = None
    project_id: Optional[int] = None
    condition_before: Optional[str] = None
    condition_after: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related data
    tool: Optional[Dict[str, Any]] = None
    project: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_tool=False, include_project=False):
        """Create DTO from model instance.

        Args:
            model: ToolCheckout model instance
            include_tool: Whether to include tool information
            include_project: Whether to include project information

        Returns:
            ToolCheckoutDTO instance
        """
        data = {
            "id": model.id,
            "tool_id": model.tool_id,
            "checked_out_by": model.checked_out_by,
            "checked_out_date": model.checked_out_date,
            "due_date": model.due_date,
            "returned_date": model.returned_date,
            "status": model.status,
            "notes": model.notes,
            "project_id": model.project_id,
            "condition_before": model.condition_before,
            "condition_after": model.condition_after,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "tool": None,
            "project": None
        }

        # Include tool information if requested
        if include_tool and hasattr(model, 'tool') and model.tool:
            from services.dto.tool_dto import ToolDTO
            data["tool"] = asdict(ToolDTO.from_model(model.tool))

        # Include project information if requested
        if include_project and hasattr(model, 'project') and model.project:
            from services.dto.project_dto import ProjectDTO
            data["project"] = asdict(ProjectDTO.from_model(model.project))

        return cls(**data)