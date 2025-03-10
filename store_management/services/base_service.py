# services/base_service.py
from contextlib import contextmanager
from typing import Any, Generator, TypeVar, Optional, List, Dict
from sqlalchemy.orm import Session
import logging

T = TypeVar('T')


class ServiceError(Exception):
    """Base exception for service-related errors."""
    pass


class ValidationError(ServiceError):
    """Exception raised when validation fails."""
    pass


class NotFoundError(ServiceError):
    """Exception raised when an entity is not found."""
    pass


class ConcurrencyError(ServiceError):
    """Exception raised when concurrent modifications conflict."""
    pass


class BaseService:
    """Base class for services with common functionality."""

    def __init__(self, session: Session):
        """Initialize the base service.

        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    @contextmanager
    def transaction(self) -> Generator[None, None, None]:
        """Provide a transactional scope around a series of operations.

        Yields:
            None

        Raises:
            Exception: If an error occurs during transaction
        """
        try:
            yield
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert an object to a dictionary.

        Args:
            obj: Object to convert

        Returns:
            Dictionary representation
        """
        if hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return obj


# services/interfaces/entity_service.py
from typing import Protocol, TypeVar, Generic, List, Optional, Dict, Any

T = TypeVar('T')


class IEntityService(Protocol, Generic[T]):
    """Generic interface for entity-related operations."""

    def get_by_id(self, entity_id: int) -> Dict[str, Any]:
        """Get entity by ID.

        Args:
            entity_id: ID of the entity to retrieve

        Returns:
            Dict representing the entity

        Raises:
            NotFoundError: If entity not found
        """
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all entities, optionally filtered.

        Args:
            filters: Optional filters to apply

        Returns:
            List of dicts representing entities
        """
        ...

    def create(self, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new entity.

        Args:
            entity_data: Dict containing entity properties

        Returns:
            Dict representing the created entity

        Raises:
            ValidationError: If validation fails
        """
        ...

    def update(self, entity_id: int, entity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing entity.

        Args:
            entity_id: ID of the entity to update
            entity_data: Dict containing updated entity properties

        Returns:
            Dict representing the updated entity

        Raises:
            NotFoundError: If entity not found
            ValidationError: If validation fails
        """
        ...

    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: ID of the entity to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If entity not found
        """
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for entities by query string.

        Args:
            query: Search query string

        Returns:
            List of dicts representing matching entities
        """
        ...


# services/interfaces/customer_service.py
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class ICustomerService(Protocol):
    """Interface for customer-related operations."""

    def get_by_id(self, customer_id: int) -> Dict[str, Any]:
        """Get customer by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all customers, optionally filtered."""
        ...

    def create(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new customer."""
        ...

    def update(self, customer_id: int, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing customer."""
        ...

    def delete(self, customer_id: int) -> bool:
        """Delete a customer by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for customers by name or email."""
        ...

    def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get customer by email address."""
        ...

    def get_sales_history(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get sales history for a customer."""
        ...

    def update_status(self, customer_id: int, status: str) -> Dict[str, Any]:
        """Update customer status."""
        ...


# services/interfaces/material_service.py
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IMaterialService(Protocol):
    """Interface for material-related operations."""

    def get_by_id(self, material_id: int) -> Dict[str, Any]:
        """Get material by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all materials, optionally filtered."""
        ...

    def create(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material."""
        ...

    def update(self, material_id: int, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing material."""
        ...

    def delete(self, material_id: int) -> bool:
        """Delete a material by ID."""
        ...

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for materials by name or other properties."""
        ...

    def get_inventory_status(self, material_id: int) -> Dict[str, Any]:
        """Get inventory status for a material."""
        ...

    def adjust_inventory(self, material_id: int, quantity: float, reason: str) -> Dict[str, Any]:
        """Adjust inventory for a material."""
        ...

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get materials by supplier ID."""
        ...

    def get_low_stock(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get materials with low stock levels."""
        ...


# services/interfaces/project_service.py
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime


class IProjectService(Protocol):
    """Interface for project-related operations."""

    def get_by_id(self, project_id: int) -> Dict[str, Any]:
        """Get project by ID."""
        ...

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get all projects, optionally filtered."""
        ...

    def create(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        ...

    def update(self, project_id: int, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing project."""
        ...

    def delete(self, project_id: int) -> bool:
        """Delete a project by ID."""
        ...

    def add_component(self, project_id: int, component_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add component to project."""
        ...

    def remove_component(self, project_id: int, component_id: int) -> bool:
        """Remove component from project."""
        ...

    def update_component(self, project_id: int, component_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update component in project."""
        ...

    def generate_picking_list(self, project_id: int) -> Dict[str, Any]:
        """Generate picking list for a project."""
        ...

    def generate_tool_list(self, project_id: int) -> Dict[str, Any]:
        """Generate tool list for a project."""
        ...

    def calculate_cost(self, project_id: int) -> Dict[str, Any]:
        """Calculate total cost for a project."""
        ...

    def update_status(self, project_id: int, status: str) -> Dict[str, Any]:
        """Update project status."""
        ...

    def get_by_customer(self, customer_id: int) -> List[Dict[str, Any]]:
        """Get projects by customer ID."""
        ...

    def get_by_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get projects within a date range."""
        ...