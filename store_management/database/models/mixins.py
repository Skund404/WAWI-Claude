from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/models/mixins.py

Mixin classes for SQLAlchemy models.
"""
logger = logging.getLogger(__name__)


class TimestampMixin:
    """
    Mixin for adding timestamp functionality to models.

    This mixin provides methods for updating timestamps on model changes.
    """

    @inject(MaterialService)
        def update_timestamp(self) -> None:
        """
        Update the updated_at timestamp.

        This method should be called before saving changes to the database.
        """
        if hasattr(self, 'updated_at'):
            self.updated_at = datetime.datetime.utcnow()


class ValidationMixin:
    """
    Mixin for adding validation functionality to models.

    This mixin provides methods for validating model data.
    """

    @inject(MaterialService)
        def validate_required_fields(self, data: Dict[str, Any],
                                 required_fields: set) -> None:
        """
        Validate that all required fields are present and not None.

        Args:
            data: Dictionary of field values to validate.
            required_fields: Set of field names that are required.

        Raises:
            ValueError: If any required field is missing or None.
        """
        for field in required_fields:
            if field not in data or data[field] is None:
                raise ValueError(f"Field '{field}' is required")

        @inject(MaterialService)
            def validate_numeric_range(self, value: float, min_val: float, max_val:
                                   float) -> None:
        """
        Validate that a numeric value is within the specified range.

        Args:
            value: The numeric value to validate.
            min_val: The minimum allowed value.
            max_val: The maximum allowed value.

        Raises:
            ValueError: If the value is outside the allowed range.
        """
        if value < min_val or value > max_val:
            raise ValueError(
                f'Value {value} must be between {min_val} and {max_val}')

        @inject(MaterialService)
            def validate_string_format(self, value: str, min_length: int,
                                   max_length: int, pattern: Optional[str] = None) -> None:
        """
        Validate that a string value meets the format requirements.

        Args:
            value: The string value to validate.
            min_length: The minimum allowed length.
            max_length: The maximum allowed length.
            pattern: Optional regex pattern that the string must match.

        Raises:
            ValueError: If the string doesn't meet the requirements.
        """
        if len(value) < min_length:
            raise ValueError(
                f'String length {len(value)} is less than minimum {min_length}'
            )
        if len(value) > max_length:
            raise ValueError(
                f'String length {len(value)} is greater than maximum {max_length}'
            )
        if pattern and not re.match(pattern, value):
            raise ValueError(
                f"String '{value}' does not match pattern '{pattern}'")


class CostingMixin:
    """
    Mixin for adding costing functionality to models.

    This mixin provides methods for calculating costs.
    """

    @inject(MaterialService)
        def calculate_labor_cost(self, hours: float, rate: float) -> float:
        """
        Calculate the labor cost.

        Args:
            hours: The number of labor hours.
            rate: The hourly labor rate.

        Returns:
            The calculated labor cost.
        """
        return hours * rate

        @inject(MaterialService)
            def calculate_overhead_cost(self, base_cost: float, overhead_rate: float
                                    ) -> float:
        """
        Calculate the overhead cost.

        Args:
            base_cost: The base cost.
            overhead_rate: The overhead rate as a percentage.

        Returns:
            The calculated overhead cost.
        """
        return base_cost * (overhead_rate / 100)

        @inject(MaterialService)
            def calculate_total_cost(self, materials_cost: float, labor_hours:
                                 float, labor_rate: float, overhead_rate: float) -> float:
        """
        Calculate the total cost including materials, labor, and overhead.

        Args:
            materials_cost: The cost of materials.
            labor_hours: The number of labor hours.
            labor_rate: The hourly labor rate.
            overhead_rate: The overhead rate as a percentage.

        Returns:
            The calculated total cost.
        """
        labor_cost = self.calculate_labor_cost(labor_hours, labor_rate)
        subtotal = materials_cost + labor_cost
        overhead_cost = self.calculate_overhead_cost(subtotal, overhead_rate)
        return subtotal + overhead_cost
