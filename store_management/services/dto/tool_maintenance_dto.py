# services/dto/tool_maintenance_dto.py
"""
Data Transfer Object for tool maintenance records.

This module defines the DTO for transferring tool maintenance data
between the service layer and the UI.
"""

import dataclasses
from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ToolMaintenanceDTO:
    """Data Transfer Object for Tool Maintenance."""

    id: int
    tool_id: int
    maintenance_type: str
    maintenance_date: datetime
    performed_by: Optional[str] = None
    cost: Optional[float] = None
    status: str = "Completed"
    details: Optional[str] = None
    parts_used: Optional[str] = None
    maintenance_interval: Optional[int] = None
    next_maintenance_date: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # Related data
    tool: Optional[Dict[str, Any]] = None

    @classmethod
    def from_model(cls, model, include_tool=False):
        """Create DTO from model instance.

        Args:
            model: ToolMaintenance model instance
            include_tool: Whether to include tool information

        Returns:
            ToolMaintenanceDTO instance
        """
        data = {
            "id": model.id,
            "tool_id": model.tool_id,
            "maintenance_type": model.maintenance_type,
            "maintenance_date": model.maintenance_date,
            "performed_by": model.performed_by,
            "cost": model.cost,
            "status": model.status,
            "details": model.details,
            "parts_used": model.parts_used,
            "maintenance_interval": model.maintenance_interval,
            "next_maintenance_date": model.next_maintenance_date,
            "created_at": model.created_at,
            "updated_at": model.updated_at,
            "tool": None
        }

        # Include tool information if requested
        if include_tool and hasattr(model, 'tool') and model.tool:
            from services.dto.tool_dto import ToolDTO
            data["tool"] = asdict(ToolDTO.from_model(model.tool))

        return cls(**data)