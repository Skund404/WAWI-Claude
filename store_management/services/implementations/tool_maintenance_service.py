# services/implementations/tool_maintenance_service.py
"""
Service implementation for tool maintenance functionality.

This service provides business logic for managing tool maintenance records,
including tracking, scheduling, and reporting on tool maintenance activities.
"""

import logging
import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session
from di.inject import inject

from database.repositories.tool_maintenance_repository import ToolMaintenanceRepository
from database.repositories.tool_repository import ToolRepository
from services.base_service import BaseService
from services.dto.tool_maintenance_dto import ToolMaintenanceDTO
from services.exceptions import NotFoundError, ValidationError


class ToolMaintenanceService(BaseService):
    """Service for managing tool maintenance records."""

    @inject
    def __init__(self, session: Session,
                 tool_maintenance_repository: ToolMaintenanceRepository,
                 tool_repository: ToolRepository):
        """Initialize the tool maintenance service.

        Args:
            session: SQLAlchemy database session
            tool_maintenance_repository: Repository for tool maintenance operations
            tool_repository: Repository for tool operations
        """
        super().__init__(session)
        self.tool_maintenance_repository = tool_maintenance_repository
        self.tool_repository = tool_repository
        self.logger = logging.getLogger(__name__)

    def get_maintenance_record_by_id(self, record_id: int, include_tool: bool = False) -> Optional[ToolMaintenanceDTO]:
        """Get a maintenance record by ID.

        Args:
            record_id: The ID of the maintenance record
            include_tool: Whether to include tool information

        Returns:
            The maintenance record DTO or None if not found

        Raises:
            NotFoundError: If the maintenance record does not exist
        """
        try:
            record = self.tool_maintenance_repository.get_by_id(record_id)
            if not record:
                raise NotFoundError(f"Maintenance record with ID {record_id} not found")

            return ToolMaintenanceDTO.from_model(record, include_tool=include_tool)
        except Exception as e:
            self.logger.error(f"Error getting maintenance record: {e}")
            raise

    def get_maintenance_records(self, criteria: Dict[str, Any] = None, offset: int = 0,
                                limit: int = 50, sort_by: str = "maintenance_date",
                                sort_dir: str = "desc", include_tool: bool = False) -> List[ToolMaintenanceDTO]:
        """Get maintenance records based on criteria.

        Args:
            criteria: Dictionary of search criteria
            offset: Pagination offset
            limit: Page size
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            include_tool: Whether to include tool information

        Returns:
            List of maintenance record DTOs

        Raises:
            ValidationError: If the criteria are invalid
        """
        try:
            # Process criteria for repository
            repo_criteria = self._process_criteria(criteria or {})

            # Get records from repository
            records = self.tool_maintenance_repository.find(
                criteria=repo_criteria,
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                sort_dir=sort_dir
            )

            # Convert to DTOs
            return [ToolMaintenanceDTO.from_model(record, include_tool=include_tool) for record in records]
        except Exception as e:
            self.logger.error(f"Error getting maintenance records: {e}")
            raise

    def count_maintenance_records(self, criteria: Dict[str, Any] = None) -> int:
        """Count maintenance records based on criteria.

        Args:
            criteria: Dictionary of search criteria

        Returns:
            The count of matching maintenance records

        Raises:
            ValidationError: If the criteria are invalid
        """
        try:
            # Process criteria for repository
            repo_criteria = self._process_criteria(criteria or {})

            # Get count from repository
            return self.tool_maintenance_repository.count(criteria=repo_criteria)
        except Exception as e:
            self.logger.error(f"Error counting maintenance records: {e}")
            raise

    def create_maintenance_record(self, data: Dict[str, Any]) -> ToolMaintenanceDTO:
        """Create a new maintenance record.

        Args:
            data: Dictionary of maintenance record data

        Returns:
            The created maintenance record DTO

        Raises:
            ValidationError: If the data is invalid
            NotFoundError: If the tool does not exist
        """
        try:
            # Validate required fields
            self._validate_maintenance_data(data)

            # Check if tool exists
            tool_id = data.get("tool_id")
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Process data for repository
            repo_data = self._process_maintenance_data(data)

            # Create record
            record = self.tool_maintenance_repository.create(repo_data)

            # Update tool's last maintenance date and next maintenance date
            tool_update = {
                "last_maintenance_date": repo_data.get("maintenance_date"),
                "next_maintenance_date": repo_data.get("next_maintenance_date")
            }
            self.tool_repository.update(tool_id, tool_update)

            # Commit changes
            self.session.commit()

            return ToolMaintenanceDTO.from_model(record, include_tool=True)
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating maintenance record: {e}")
            raise

    def update_maintenance_record(self, record_id: int, data: Dict[str, Any]) -> ToolMaintenanceDTO:
        """Update an existing maintenance record.

        Args:
            record_id: The ID of the maintenance record to update
            data: Dictionary of maintenance record data

        Returns:
            The updated maintenance record DTO

        Raises:
            NotFoundError: If the maintenance record does not exist
            ValidationError: If the data is invalid
        """
        try:
            # Check if record exists
            record = self.tool_maintenance_repository.get_by_id(record_id)
            if not record:
                raise NotFoundError(f"Maintenance record with ID {record_id} not found")

            # Process data for repository
            repo_data = self._process_maintenance_data(data)

            # Update record
            updated_record = self.tool_maintenance_repository.update(record_id, repo_data)

            # If status is changed to "Completed", update tool's last maintenance date
            if repo_data.get("status") == "Completed" and record.status != "Completed":
                tool_update = {
                    "last_maintenance_date": repo_data.get("maintenance_date") or datetime.datetime.now(),
                    "next_maintenance_date": repo_data.get("next_maintenance_date")
                }
                self.tool_repository.update(record.tool_id, tool_update)

            # Commit changes
            self.session.commit()

            return ToolMaintenanceDTO.from_model(updated_record, include_tool=True)
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error updating maintenance record: {e}")
            raise

    def delete_maintenance_record(self, record_id: int) -> bool:
        """Delete a maintenance record.

        Args:
            record_id: The ID of the maintenance record to delete

        Returns:
            True if deleted successfully

        Raises:
            NotFoundError: If the maintenance record does not exist
        """
        try:
            # Check if record exists
            record = self.tool_maintenance_repository.get_by_id(record_id)
            if not record:
                raise NotFoundError(f"Maintenance record with ID {record_id} not found")

            # Delete record
            self.tool_maintenance_repository.delete(record_id)

            # Commit changes
            self.session.commit()

            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error deleting maintenance record: {e}")
            raise

    def complete_maintenance(self, record_id: int) -> ToolMaintenanceDTO:
        """Mark a maintenance record as completed.

        Args:
            record_id: The ID of the maintenance record

        Returns:
            The updated maintenance record DTO

        Raises:
            NotFoundError: If the maintenance record does not exist
        """
        try:
            # Check if record exists
            record = self.tool_maintenance_repository.get_by_id(record_id)
            if not record:
                raise NotFoundError(f"Maintenance record with ID {record_id} not found")

            # Update status to completed
            data = {
                "status": "Completed",
                "maintenance_date": datetime.datetime.now()
            }

            # Calculate next maintenance date if interval is set
            if record.maintenance_interval:
                data["next_maintenance_date"] = datetime.datetime.now() + datetime.timedelta(
                    days=record.maintenance_interval)

            # Update record
            updated_record = self.tool_maintenance_repository.update(record_id, data)

            # Update tool's last maintenance date and next maintenance date
            tool_update = {
                "last_maintenance_date": data.get("maintenance_date"),
                "next_maintenance_date": data.get("next_maintenance_date")
            }
            self.tool_repository.update(record.tool_id, tool_update)

            # Commit changes
            self.session.commit()

            return ToolMaintenanceDTO.from_model(updated_record, include_tool=True)
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error completing maintenance record: {e}")
            raise

    def get_maintenance_statistics(self, tool_id: Optional[int] = None) -> Dict[str, Any]:
        """Get maintenance statistics.

        Args:
            tool_id: Optional tool ID to filter statistics for a specific tool

        Returns:
            Dictionary of maintenance statistics
        """
        try:
            # Initialize statistics
            stats = {
                "upcoming": 0,
                "overdue": 0,
                "this_month": 0,
                "total_cost": 0.0
            }

            # Build criteria
            criteria = {}
            if tool_id:
                criteria["tool_id"] = tool_id

            # Get all maintenance records for calculation
            all_records = self.tool_maintenance_repository.find(criteria=criteria, limit=1000)

            # Current date for comparisons
            now = datetime.datetime.now()
            month_start = datetime.datetime(now.year, now.month, 1)
            month_end = (month_start + datetime.timedelta(days=32)).replace(day=1) - datetime.timedelta(seconds=1)

            # Calculate statistics
            for record in all_records:
                # Completed maintenance this month
                if (record.status == "Completed" and
                        record.maintenance_date and
                        month_start <= record.maintenance_date <= month_end):
                    stats["this_month"] += 1

                # Add cost to total
                if record.cost:
                    stats["total_cost"] += record.cost

                # Upcoming maintenance (scheduled in the future)
                if (record.status != "Completed" and record.status != "Cancelled" and
                        record.next_maintenance_date and record.next_maintenance_date > now):
                    stats["upcoming"] += 1

                # Overdue maintenance (scheduled in the past)
                if (record.status != "Completed" and record.status != "Cancelled" and
                        record.next_maintenance_date and record.next_maintenance_date < now):
                    stats["overdue"] += 1

            return stats
        except Exception as e:
            self.logger.error(f"Error getting maintenance statistics: {e}")
            raise

    def _process_criteria(self, criteria: Dict[str, Any]) -> Dict[str, Any]:
        """Process search criteria for the repository.

        Args:
            criteria: The original search criteria

        Returns:
            Processed criteria for the repository
        """
        repo_criteria = {}

        # Map UI field names to repository field names
        field_mapping = {
            "tool_name": "tool.name",
            "date_from": "maintenance_date",
            "date_to": "maintenance_date",
            "technician": "performed_by"
        }

        # Process each criterion
        for key, value in criteria.items():
            if not value:
                continue

            if key == "date_from":
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                    repo_criteria["maintenance_date__gte"] = date
                except ValueError:
                    pass
            elif key == "date_to":
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                    # Set to end of day
                    date = date.replace(hour=23, minute=59, second=59)
                    repo_criteria["maintenance_date__lte"] = date
                except ValueError:
                    pass
            elif key in field_mapping:
                repo_criteria[field_mapping[key]] = value
            else:
                repo_criteria[key] = value

        return repo_criteria

    def _validate_maintenance_data(self, data: Dict[str, Any]):
        """Validate maintenance record data.

        Args:
            data: The maintenance record data to validate

        Raises:
            ValidationError: If the data is invalid
        """
        # Check required fields
        required_fields = ["tool_id", "maintenance_type", "maintenance_date", "status"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]

        if missing_fields:
            fields_str = ", ".join(missing_fields)
            raise ValidationError(f"Missing required fields: {fields_str}")

        # Validate tool_id is an integer
        try:
            int(data["tool_id"])
        except (ValueError, TypeError):
            raise ValidationError("Tool ID must be a valid integer")

    def _process_maintenance_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process maintenance record data for the repository.

        Args:
            data: The original maintenance record data

        Returns:
            Processed data for the repository
        """
        repo_data = {}

        # Copy valid fields
        valid_fields = [
            "tool_id", "maintenance_type", "maintenance_date", "performed_by",
            "cost", "status", "details", "parts_used", "maintenance_interval",
            "next_maintenance_date"
        ]

        for field in valid_fields:
            if field in data:
                repo_data[field] = data[field]

        # Convert dates from string to datetime if needed
        date_fields = ["maintenance_date", "next_maintenance_date"]
        for field in date_fields:
            if field in repo_data and isinstance(repo_data[field], str):
                try:
                    repo_data[field] = datetime.datetime.strptime(repo_data[field], "%Y-%m-%d")
                except ValueError:
                    del repo_data[field]

        # Calculate next maintenance date if interval provided and not explicitly set
        if ("maintenance_interval" in repo_data and repo_data["maintenance_interval"] and
                "maintenance_date" in repo_data and
                "next_maintenance_date" not in repo_data):
            interval = repo_data["maintenance_interval"]
            date = repo_data["maintenance_date"]
            repo_data["next_maintenance_date"] = date + datetime.timedelta(days=interval)

        return repo_data