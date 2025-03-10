# services/base_service.py
# Base service implementation with common functionality

from contextlib import contextmanager
from typing import Generator, Any, Dict, List, Optional, TypeVar, Generic
from sqlalchemy.orm import Session
import logging

T = TypeVar('T')


class BaseService:
    """Base class for services with common functionality.

    Provides common methods for transaction management, logging, and error handling
    that will be used by all service implementations.
    """

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
            self.logger.debug("Transaction committed successfully")
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Transaction rolled back due to error: {str(e)}")
            raise

    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str], update: bool = False) -> None:
        """Validate that required fields are present in the data.

        Args:
            data: Data to validate
            required_fields: List of required field names
            update: Whether this is an update operation (if True, fields are optional)

        Raises:
            ValidationError: If a required field is missing
        """
        if not update:  # Only require fields for new entities
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

    def _validate_enum_value(self, enum_class: Any, value: str, field_name: str) -> None:
        """Validate that a value is a valid enum value.

        Args:
            enum_class: Enum class to validate against
            value: Value to validate
            field_name: Name of the field for error message

        Raises:
            ValidationError: If the value is not a valid enum value
        """
        if value is not None:
            try:
                enum_class(value)
            except ValueError:
                raise ValidationError(f"Invalid {field_name}: {value}")

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