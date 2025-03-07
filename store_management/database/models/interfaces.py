# database/models/interfaces.py
"""
Comprehensive Interface Definitions for Leatherworking Management System

This module defines interfaces and abstract base classes that establish
consistent APIs across related model types, facilitating polymorphic handling
and ensuring implementation consistency.
"""

import abc
from datetime import datetime
from typing import Any, Dict, Optional, List, Union, TypeVar, Generic, Type

from database.models.enums import (
    InventoryStatus,
    ProjectStatus,
    SaleStatus,
    PaymentStatus,
    TransactionType
)

# Type variable for generic model interfaces
T = TypeVar('T')


class IModel(abc.ABC):
    """
    Core interface for all database models providing essential operations.
    """

    @abc.abstractmethod
    def to_dict(self, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Convert model instance to a dictionary representation.

        Args:
            exclude_fields: Optional list of fields to exclude from the dictionary

        Returns:
            Dictionary representation of the model
        """
        pass

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IModel':
        """
        Create a new model instance from dictionary data.

        Args:
            data: Dictionary containing model attributes

        Returns:
            A new model instance
        """
        pass

    @abc.abstractmethod
    def validate(self) -> Dict[str, List[str]]:
        """
        Validate the current model instance.

        Returns:
            Dictionary mapping field names to validation error messages,
            or an empty dictionary if validation succeeds
        """
        pass

    @abc.abstractmethod
    def is_valid(self) -> bool:
        """
        Check if the model instance is valid.

        Returns:
            True if the model is valid, False otherwise
        """
        pass


class IProject(IModel):
    """
    Interface for project-related models establishing project management API.
    """

    @abc.abstractmethod
    def update_status(self, new_status: Union[str, ProjectStatus]) -> None:
        """
        Update the project status with validation.

        Args:
            new_status: New status for the project, either as string or enum

        Raises:
            ValueError: If the status is invalid
        """
        pass

    @abc.abstractmethod
    def add_component(self, component: Any, quantity: float = 1.0) -> Any:
        """
        Add a component to the project.

        Args:
            component: Component to add to the project
            quantity: Quantity of the component

        Returns:
            The created project-component relationship
        """
        pass

    @abc.abstractmethod
    def calculate_total_cost(self) -> float:
        """
        Calculate the total cost of the project.

        Returns:
            Total cost value
        """
        pass

    @abc.abstractmethod
    def get_timeline(self) -> Dict[str, datetime]:
        """
        Get project timeline information.

        Returns:
            Dictionary with timeline information (start_date, due_date, etc.)
        """
        pass


class IInventoryItem(IModel):
    """
    Interface for inventory-related models establishing inventory management API.
    """

    @abc.abstractmethod
    def adjust_quantity(self, quantity_change: float,
                       transaction_type: Union[str, TransactionType],
                       notes: Optional[str] = None) -> None:
        """
        Adjust the quantity of the inventory item.

        Args:
            quantity_change: Amount to adjust the quantity by (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Raises:
            ValueError: If the resulting quantity would be negative
        """
        pass

    @abc.abstractmethod
    def get_stock_value(self) -> float:
        """
        Calculate the total stock value.

        Returns:
            Total value of the item in stock
        """
        pass

    @abc.abstractmethod
    def update_status(self, new_status: Union[str, InventoryStatus]) -> None:
        """
        Manually update the inventory status.

        Args:
            new_status: New status for the inventory item

        Raises:
            ValueError: If the status is invalid
        """
        pass

    @abc.abstractmethod
    def needs_reorder(self) -> bool:
        """
        Check if the inventory item needs to be reordered.

        Returns:
            True if the item needs to be reordered, False otherwise
        """
        pass


class ISalesItem(IModel):
    """
    Interface for sales-related models establishing sales management API.
    """

    @abc.abstractmethod
    def update_status(self, new_status: Union[str, SaleStatus]) -> None:
        """
        Update the sales status.

        Args:
            new_status: New status for the sale

        Raises:
            ValueError: If the status is invalid
        """
        pass

    @abc.abstractmethod
    def update_payment_status(self, new_status: Union[str, PaymentStatus]) -> None:
        """
        Update the payment status.

        Args:
            new_status: New payment status

        Raises:
            ValueError: If the status is invalid
        """
        pass

    @abc.abstractmethod
    def calculate_total(self) -> float:
        """
        Calculate the total amount for the sale.

        Returns:
            Total sales amount
        """
        pass


class IFactory(Generic[T]):
    """
    Interface for factory classes that create model instances.
    """

    @classmethod
    @abc.abstractmethod
    def create(cls, data: Dict[str, Any]) -> T:
        """
        Create a model instance with validation.

        Args:
            data: Dictionary containing model attributes

        Returns:
            A new model instance

        Raises:
            ValueError: If the data is invalid
        """
        pass

    @classmethod
    @abc.abstractmethod
    def _validate(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and preprocess input data before model creation.

        Args:
            data: Raw data to validate

        Returns:
            Processed and validated data

        Raises:
            ValueError: If the data is invalid
        """
        pass


class IRepository(Generic[T]):
    """
    Interface for repository classes that handle data access operations.
    """

    @abc.abstractmethod
    def get(self, id: int) -> Optional[T]:
        """
        Get a model instance by ID.

        Args:
            id: The ID of the model to retrieve

        Returns:
            The model instance or None if not found
        """
        pass

    @abc.abstractmethod
    def get_all(self) -> List[T]:
        """
        Get all model instances.

        Returns:
            List of all model instances
        """
        pass

    @abc.abstractmethod
    def save(self, model: T) -> T:
        """
        Save a model instance.

        Args:
            model: The model instance to save

        Returns:
            The saved model instance
        """
        pass

    @abc.abstractmethod
    def delete(self, id: int) -> bool:
        """
        Delete a model instance by ID.

        Args:
            id: The ID of the model to delete

        Returns:
            True if the model was deleted, False otherwise
        """
        pass


# Utility functions for model interfaces

def validate_model_data(data: Dict[str, Any], required_fields: Optional[List[str]] = None,
                       field_validators: Optional[Dict[str, callable]] = None) -> Dict[str, List[str]]:
    """
    Generic comprehensive data validation function for model data.

    Args:
        data: Data to validate
        required_fields: List of required field names
        field_validators: Dictionary mapping field names to validator functions

    Returns:
        Dictionary mapping field names to validation error messages,
        or an empty dictionary if validation succeeds
    """
    errors = {}

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.setdefault(field, []).append(f"{field} is required")

    # Apply field-specific validators
    if field_validators:
        for field, validator in field_validators.items():
            if field in data:
                try:
                    validation_result = validator(data[field])
                    if validation_result is not None:
                        errors.setdefault(field, []).append(validation_result)
                except Exception as e:
                    errors.setdefault(field, []).append(str(e))

    return errors


def convert_dict_to_model(data: Dict[str, Any], model_class: Type[T]) -> T:
    """
    Convert a dictionary to a model instance.

    Args:
        data: Dictionary containing model attributes
        model_class: The model class to instantiate

    Returns:
        A new model instance

    Raises:
        ValueError: If the data is invalid
    """
    try:
        return model_class(**data)
    except Exception as e:
        raise ValueError(f"Failed to convert data to {model_class.__name__}: {str(e)}")


def convert_model_to_dict(model: Any, exclude_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Generic implementation of converting a model to a dictionary.

    Args:
        model: The model instance to convert
        exclude_fields: Optional list of fields to exclude

    Returns:
        Dictionary representation of the model
    """
    if exclude_fields is None:
        exclude_fields = []

    # Add standard fields to exclude
    exclude_fields.extend(['_sa_instance_state'])

    return {
        key: value for key, value in model.__dict__.items()
        if not key.startswith('_') and key not in exclude_fields
    }