# services/implementations/tool_checkout_service.py
"""
Service implementation for tool checkout functionality.

This service provides business logic for managing tool checkouts,
including checking tools in and out, tracking overdue tools,
and generating reports on tool usage.
"""

import logging
import datetime
from typing import Any, Dict, List, Optional, Union

from sqlalchemy.orm import Session
from di.inject import inject

from database.repositories.tool_checkout_repository import ToolCheckoutRepository
from database.repositories.tool_repository import ToolRepository
from database.repositories.project_repository import ProjectRepository
from database.models.enums import InventoryStatus
from services.base_service import BaseService
from services.dto.tool_checkout_dto import ToolCheckoutDTO
from services.exceptions import NotFoundError, ValidationError, BusinessRuleError


class ToolCheckoutService(BaseService):
    """Service for managing tool checkouts."""

    @inject
    def __init__(self, session: Session,
                 tool_checkout_repository: ToolCheckoutRepository,
                 tool_repository: ToolRepository,
                 project_repository: ProjectRepository):
        """Initialize the tool checkout service.

        Args:
            session: SQLAlchemy database session
            tool_checkout_repository: Repository for tool checkout operations
            tool_repository: Repository for tool operations
            project_repository: Repository for project operations
        """
        super().__init__(session)
        self.tool_checkout_repository = tool_checkout_repository
        self.tool_repository = tool_repository
        self.project_repository = project_repository
        self.logger = logging.getLogger(__name__)

    def get_checkout_by_id(self, checkout_id: int, include_tool: bool = False,
                           include_project: bool = False) -> Optional[ToolCheckoutDTO]:
        """Get a checkout record by ID.

        Args:
            checkout_id: The ID of the checkout record
            include_tool: Whether to include tool information
            include_project: Whether to include project information

        Returns:
            The checkout record DTO or None if not found

        Raises:
            NotFoundError: If the checkout record does not exist
        """
        try:
            checkout = self.tool_checkout_repository.get_by_id(checkout_id)
            if not checkout:
                raise NotFoundError(f"Checkout record with ID {checkout_id} not found")

            return ToolCheckoutDTO.from_model(
                checkout,
                include_tool=include_tool,
                include_project=include_project
            )
        except Exception as e:
            self.logger.error(f"Error getting checkout record: {e}")
            raise

    def get_checkouts(self, criteria: Dict[str, Any] = None, offset: int = 0,
                      limit: int = 50, sort_by: str = "checked_out_date",
                      sort_dir: str = "desc", include_tool: bool = False,
                      include_project: bool = False) -> List[ToolCheckoutDTO]:
        """Get checkout records based on criteria.

        Args:
            criteria: Dictionary of search criteria
            offset: Pagination offset
            limit: Page size
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            include_tool: Whether to include tool information
            include_project: Whether to include project information

        Returns:
            List of checkout record DTOs

        Raises:
            ValidationError: If the criteria are invalid
        """
        try:
            # Process criteria for repository
            repo_criteria = self._process_criteria(criteria or {})

            # Get records from repository
            checkouts = self.tool_checkout_repository.find(
                criteria=repo_criteria,
                offset=offset,
                limit=limit,
                sort_by=sort_by,
                sort_dir=sort_dir
            )

            # Convert to DTOs
            return [
                ToolCheckoutDTO.from_model(
                    checkout,
                    include_tool=include_tool,
                    include_project=include_project
                )
                for checkout in checkouts
            ]
        except Exception as e:
            self.logger.error(f"Error getting checkout records: {e}")
            raise

    def count_checkouts(self, criteria: Dict[str, Any] = None) -> int:
        """Count checkout records based on criteria.

        Args:
            criteria: Dictionary of search criteria

        Returns:
            The count of matching checkout records

        Raises:
            ValidationError: If the criteria are invalid
        """
        try:
            # Process criteria for repository
            repo_criteria = self._process_criteria(criteria or {})

            # Get count from repository
            return self.tool_checkout_repository.count(criteria=repo_criteria)
        except Exception as e:
            self.logger.error(f"Error counting checkout records: {e}")
            raise

    def checkout_tool(self, tool_id: int, data: Dict[str, Any]) -> ToolCheckoutDTO:
        """Check out a tool.

        Args:
            tool_id: The ID of the tool to check out
            data: Dictionary of checkout data

        Returns:
            The created checkout record DTO

        Raises:
            ValidationError: If the data is invalid
            NotFoundError: If the tool does not exist
            BusinessRuleError: If the tool is already checked out
        """
        try:
            # Validate required fields
            self._validate_checkout_data(data)

            # Check if tool exists
            tool = self.tool_repository.get_by_id(tool_id)
            if not tool:
                raise NotFoundError(f"Tool with ID {tool_id} not found")

            # Check if tool is available
            active_checkouts = self.tool_checkout_repository.find(
                criteria={"tool_id": tool_id, "status__in": ["checked_out", "overdue"]}
            )

            if active_checkouts:
                raise BusinessRuleError(f"Tool '{tool.name}' is already checked out")

            # Process data for repository
            repo_data = data.copy()
            repo_data["tool_id"] = tool_id

            # Set default values
            if "checked_out_date" not in repo_data:
                repo_data["checked_out_date"] = datetime.datetime.now()

            if "status" not in repo_data:
                repo_data["status"] = "checked_out"

            # Validate project if provided
            if "project_id" in repo_data and repo_data["project_id"]:
                project = self.project_repository.get_by_id(repo_data["project_id"])
                if not project:
                    raise NotFoundError(f"Project with ID {repo_data['project_id']} not found")

            # Create checkout record
            checkout = self.tool_checkout_repository.create(repo_data)

            # Update tool's status to "checked_out"
            self.tool_repository.update(tool_id, {"status": "CHECKED_OUT"})

            # Commit changes
            self.session.commit()

            return ToolCheckoutDTO.from_model(checkout, include_tool=True, include_project=True)
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error checking out tool: {e}")
            raise

    def check_in_tool(self, checkout_id: int, data: Dict[str, Any]) -> ToolCheckoutDTO:
        """Check in a tool.

        Args:
            checkout_id: The ID of the checkout record
            data: Dictionary of check-in data

        Returns:
            The updated checkout record DTO

        Raises:
            NotFoundError: If the checkout record does not exist
            ValidationError: If the data is invalid
            BusinessRuleError: If the tool is already checked in
        """
        try:
            # Check if checkout record exists
            checkout = self.tool_checkout_repository.get_by_id(checkout_id)
            if not checkout:
                raise NotFoundError(f"Checkout record with ID {checkout_id} not found")

            # Check if tool is already checked in
            if checkout.status == "returned":
                raise BusinessRuleError("Tool is already checked in")

            # Process data for repository
            repo_data = data.copy()

            # Set default values
            if "returned_date" not in repo_data:
                repo_data["returned_date"] = datetime.datetime.now()

            repo_data["status"] = "returned"

            # Update checkout record
            updated_checkout = self.tool_checkout_repository.update(checkout_id, repo_data)

            # Update tool's status to "IN_STOCK"
            self.tool_repository.update(checkout.tool_id, {"status": "IN_STOCK"})

            # Commit changes
            self.session.commit()

            return ToolCheckoutDTO.from_model(updated_checkout, include_tool=True, include_project=True)
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error checking in tool: {e}")
            raise

    def report_tool_problem(self, checkout_id: int, problem_type: str, notes: str) -> ToolCheckoutDTO:
        """Report a problem with a checked out tool.

        Args:
            checkout_id: The ID of the checkout record
            problem_type: The type of problem (lost, damaged)
            notes: Notes about the problem

        Returns:
            The updated checkout record DTO

        Raises:
            NotFoundError: If the checkout record does not exist
            ValidationError: If the data is invalid
            BusinessRuleError: If the tool is already checked in
        """
        try:
            # Check if checkout record exists
            checkout = self.tool_checkout_repository.get_by_id(checkout_id)
            if not checkout:
                raise NotFoundError(f"Checkout record with ID {checkout_id} not found")

            # Check if tool is already checked in
            if checkout.status == "returned":
                raise BusinessRuleError("Tool is already checked in")

            # Validate problem type
            valid_problem_types = ["lost", "damaged"]
            if problem_type not in valid_problem_types:
                raise ValidationError(
                    f"Invalid problem type: {problem_type}. Valid types are: {', '.join(valid_problem_types)}")

            # Update checkout record
            data = {
                "status": problem_type,
                "notes": notes
            }

            updated_checkout = self.tool_checkout_repository.update(checkout_id, data)

            # Update tool's status based on problem type
            tool_status = "LOST" if problem_type == "lost" else "DAMAGED"
            self.tool_repository.update(checkout.tool_id, {"status": tool_status})

            # Commit changes
            self.session.commit()

            return ToolCheckoutDTO.from_model(updated_checkout, include_tool=True, include_project=True)
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error reporting tool problem: {e}")
            raise

    def get_checked_out_tools(self, include_overdue: bool = True) -> List[ToolCheckoutDTO]:
        """Get all checked out tools.

        Args:
            include_overdue: Whether to include overdue tools

        Returns:
            List of checkout record DTOs for checked out tools
        """
        try:
            # Set criteria
            criteria = {}
            if include_overdue:
                criteria["status__in"] = ["checked_out", "overdue"]
            else:
                criteria["status"] = "checked_out"

            # Get records from repository
            checkouts = self.tool_checkout_repository.find(
                criteria=criteria,
                sort_by="checked_out_date",
                sort_dir="desc"
            )

            # Update status for any overdue tools
            now = datetime.datetime.now()
            for checkout in checkouts:
                if checkout.due_date and now > checkout.due_date and checkout.status != "overdue":
                    checkout.status = "overdue"
                    self.tool_checkout_repository.update(checkout.id, {"status": "overdue"})

            # Commit any status updates
            if any(checkout.status == "overdue" for checkout in checkouts):
                self.session.commit()

            # Convert to DTOs
            return [
                ToolCheckoutDTO.from_model(checkout, include_tool=True, include_project=True)
                for checkout in checkouts
            ]
        except Exception as e:
            self.logger.error(f"Error getting checked out tools: {e}")
            raise

    def get_checkout_statistics(self) -> Dict[str, Any]:
        """Get checkout statistics.

        Returns:
            Dictionary of checkout statistics
        """
        try:
            # Initialize statistics
            stats = {
                "total_active": 0,
                "overdue": 0,
                "checkout_count_today": 0,
                "return_count_today": 0,
                "most_used_tools": []
            }

            # Calculate statistics
            now = datetime.datetime.now()
            today_start = datetime.datetime(now.year, now.month, now.day)
            today_end = today_start + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

            # Count active checkouts
            active_checkouts = self.tool_checkout_repository.find(
                criteria={"status__in": ["checked_out", "overdue"]}
            )
            stats["total_active"] = len(active_checkouts)

            # Count overdue checkouts
            overdue_checkouts = [c for c in active_checkouts if c.status == "overdue" or
                                 (c.due_date and now > c.due_date)]
            stats["overdue"] = len(overdue_checkouts)

            # Count today's checkouts
            today_checkouts = self.tool_checkout_repository.find(
                criteria={"checked_out_date__gte": today_start, "checked_out_date__lte": today_end}
            )
            stats["checkout_count_today"] = len(today_checkouts)

            # Count today's returns
            today_returns = self.tool_checkout_repository.find(
                criteria={"returned_date__gte": today_start, "returned_date__lte": today_end}
            )
            stats["return_count_today"] = len(today_returns)

            # Get most used tools (top 5)
            # This would likely need a custom repository method for efficiency
            # For now, we'll leave it empty
            stats["most_used_tools"] = []

            return stats
        except Exception as e:
            self.logger.error(f"Error getting checkout statistics: {e}")
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
            "checked_out_from": "checked_out_date",
            "checked_out_to": "checked_out_date",
            "due_from": "due_date",
            "due_to": "due_date",
            "user": "checked_out_by"
        }

        # Process each criterion
        for key, value in criteria.items():
            if not value:
                continue

            if key == "checked_out_from":
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                    repo_criteria["checked_out_date__gte"] = date
                except ValueError:
                    pass
            elif key == "checked_out_to":
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                    # Set to end of day
                    date = date.replace(hour=23, minute=59, second=59)
                    repo_criteria["checked_out_date__lte"] = date
                except ValueError:
                    pass
            elif key == "due_from":
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                    repo_criteria["due_date__gte"] = date
                except ValueError:
                    pass
            elif key == "due_to":
                try:
                    date = datetime.datetime.strptime(value, "%Y-%m-%d")
                    # Set to end of day
                    date = date.replace(hour=23, minute=59, second=59)
                    repo_criteria["due_date__lte"] = date
                except ValueError:
                    pass
            elif key in field_mapping:
                repo_criteria[field_mapping[key]] = value
            else:
                repo_criteria[key] = value

        return repo_criteria

    def _validate_checkout_data(self, data: Dict[str, Any]):
        """Validate checkout data.

        Args:
            data: The checkout data to validate

        Raises:
            ValidationError: If the data is invalid
        """
        # Check required fields
        required_fields = ["checked_out_by"]
        missing_fields = [field for field in required_fields if field not in data or not data[field]]

        if missing_fields:
            fields_str = ", ".join(missing_fields)
            raise ValidationError(f"Missing required fields: {fields_str}")

        # Validate date formats
        date_fields = ["checked_out_date", "due_date", "returned_date"]
        for field in date_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.datetime.strptime(data[field], "%Y-%m-%d")
                except ValueError:
                    raise ValidationError(f"Invalid date format for {field}. Use YYYY-MM-DD format.")