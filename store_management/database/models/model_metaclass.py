# database/models/model_metaclass.py
"""
Comprehensive Model Metaclass for Leatherworking Management System

This module defines advanced metaclass capabilities for enhancing model
behaviors, tracking model registrations, and managing complex inheritance
relationships across the application.
"""

import logging
from abc import ABCMeta
from types import FunctionType
from typing import Any, Dict, Type, Optional, List, Set, ClassVar, Tuple, Union, Callable

from sqlalchemy.orm import DeclarativeBase, registry
from sqlalchemy.exc import SQLAlchemyError

from utils.circular_import_resolver import CircularImportResolver

# Setup logger
logger = logging.getLogger(__name__)


class ModelRegistryMixin:
    """
    Mixin providing model registry capabilities for tracking and managing models.
    """
    # Class variables for model tracking
    _registered_models: Dict[str, Type] = {}
    _model_metadata: Dict[str, Dict[str, Any]] = {}
    _dependency_graph: Dict[str, Set[str]] = {}

    @classmethod
    def register_model(cls, model_class: Type, model_name: Optional[str] = None) -> None:
        """
        Register a model class in the central registry.

        Args:
            model_class: The model class to register
            model_name: Optional custom name for the model (defaults to class name)
        """
        name = model_name or model_class.__name__
        cls._registered_models[name] = model_class

        # Store metadata about the model
        cls._model_metadata[name] = {
            'module': model_class.__module__,
            'tablename': getattr(model_class, '__tablename__', None),
            'registration_time': __import__('datetime').datetime.utcnow()
        }

        logger.debug(f"Registered model: {name} from {model_class.__module__}")

    @classmethod
    def get_model(cls, model_name: str) -> Optional[Type]:
        """
        Retrieve a registered model by name.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            The model class or None if not found
        """
        return cls._registered_models.get(model_name)

    @classmethod
    def list_registered_models(cls) -> List[str]:
        """
        Get a list of all registered model names.

        Returns:
            List of registered model names
        """
        return list(cls._registered_models.keys())

    @classmethod
    def get_model_metadata(cls, model_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary of model metadata
        """
        return cls._model_metadata.get(model_name, {})


class ModelValidationMixin:
    """
    Mixin providing model validation capabilities.
    """
    # Class variables for validation rules
    _validation_rules: Dict[str, Dict[str, Callable]] = {}

    @classmethod
    def register_validation_rule(cls, model_name: str, field_name: str, rule: Callable) -> None:
        """
        Register a validation rule for a specific model field.

        Args:
            model_name: Name of the model
            field_name: Name of the field to validate
            rule: Validation function taking the field value and returning a bool or error message
        """
        if model_name not in cls._validation_rules:
            cls._validation_rules[model_name] = {}

        cls._validation_rules[model_name][field_name] = rule
        logger.debug(f"Registered validation rule for {model_name}.{field_name}")

    @classmethod
    def get_validation_rules(cls, model_name: str) -> Dict[str, Callable]:
        """
        Get all validation rules for a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary mapping field names to validation functions
        """
        return cls._validation_rules.get(model_name, {})

    @classmethod
    def validate_model_data(cls, model_name: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
        """
        Validate a dictionary of model data against registered rules.

        Args:
            model_name: Name of the model to validate against
            data: Dictionary of field values to validate

        Returns:
            Tuple of (is_valid, error_dict)
        """
        is_valid = True
        errors = {}

        for field, rule in cls.get_validation_rules(model_name).items():
            if field in data:
                try:
                    result = rule(data[field])
                    # If result is a string, it's an error message
                    if isinstance(result, str):
                        errors.setdefault(field, []).append(result)
                        is_valid = False
                    # If result is False, there's an error
                    elif result is False:
                        errors.setdefault(field, []).append(f"Invalid value for {field}")
                        is_valid = False
                except Exception as e:
                    errors.setdefault(field, []).append(f"Validation error: {str(e)}")
                    is_valid = False

        return is_valid, errors


class ModelRelationshipMixin:
    """
    Mixin providing model relationship management capabilities.
    """
    # Class variables for relationship tracking
    _relationship_initializers: Dict[str, List[Callable]] = {}
    _deferred_relationships: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def register_relationship_initializer(cls, model_name: str, initializer: Callable) -> None:
        """
        Register a function to initialize relationships for a model.

        Args:
            model_name: Name of the model
            initializer: Function that initializes relationships
        """
        if model_name not in cls._relationship_initializers:
            cls._relationship_initializers[model_name] = []

        cls._relationship_initializers[model_name].append(initializer)
        logger.debug(f"Registered relationship initializer for {model_name}")

    @classmethod
    def initialize_relationships(cls, model_name: str) -> None:
        """
        Execute all registered relationship initializers for a model.

        Args:
            model_name: Name of the model
        """
        initializers = cls._relationship_initializers.get(model_name, [])
        for initializer in initializers:
            try:
                initializer()
                logger.debug(f"Initialized relationships for {model_name}")
            except Exception as e:
                logger.error(f"Error initializing relationships for {model_name}: {e}")

    @classmethod
    def initialize_all_relationships(cls) -> None:
        """
        Initialize relationships for all registered models.
        """
        for model_name in cls._relationship_initializers:
            cls.initialize_relationships(model_name)

        # Process any deferred relationships
        cls._process_deferred_relationships()

        logger.info("Initialized all model relationships")

    @classmethod
    def defer_relationship(cls, model_name: str, relationship_name: str, target_model: str) -> None:
        """
        Defer a relationship that needs to be resolved later.

        Args:
            model_name: Source model name
            relationship_name: Name of the relationship to establish
            target_model: Target model name
        """
        if model_name not in cls._deferred_relationships:
            cls._deferred_relationships[model_name] = {}

        cls._deferred_relationships[model_name][relationship_name] = target_model
        logger.debug(f"Deferred relationship: {model_name}.{relationship_name} -> {target_model}")

    @classmethod
    def _process_deferred_relationships(cls) -> None:
        """
        Process all deferred relationships after all models are registered.
        """
        try:
            for model_name, relationships in cls._deferred_relationships.items():
                model_class = cls.get_model(model_name)
                if not model_class:
                    logger.warning(f"Cannot resolve deferred relationships - model {model_name} not found")
                    continue

                for rel_name, target_model in relationships.items():
                    target_class = cls.get_model(target_model)
                    if not target_class:
                        logger.warning(f"Cannot resolve deferred relationship - target {target_model} not found")
                        continue

                    # Create the relationship dynamically
                    # In practice, this would involve setting up SQLAlchemy relationships
                    logger.debug(f"Resolved deferred relationship: {model_name}.{rel_name} -> {target_model}")
        except Exception as e:
            logger.error(f"Error processing deferred relationships: {e}")


class BaseModelMetaclass(ABCMeta, ModelRegistryMixin, ModelValidationMixin, ModelRelationshipMixin):
    """
    Advanced metaclass for enhancing model capabilities with validation,
    registration, and relationship management.
    """

    def __new__(mcs, name: str, bases: tuple, attrs: Dict[str, Any]) -> Type:
        """
        Custom metaclass __new__ method to enhance model class creation.

        Args:
            name: Name of the class being created
            bases: Base classes
            attrs: Class attributes

        Returns:
            Enhanced model class
        """
        # Skip processing for the base classes themselves
        if name in ['BaseModel', 'Base', 'DeclarativeBase']:
            return super().__new__(mcs, name, bases, attrs)

        # Create the class
        cls = super().__new__(mcs, name, bases, attrs)

        # Auto-register non-abstract models
        if not attrs.get('__abstract__', False):
            mcs.register_model(cls)

            # Register model with CircularImportResolver if available
            try:
                if hasattr(CircularImportResolver, 'register_model'):
                    CircularImportResolver.register_model(name, cls, cls.__module__)
            except Exception as e:
                logger.warning(f"Could not register model with CircularImportResolver: {e}")

        # Process any validation methods
        for attr_name, attr_value in attrs.items():
            # Find validation methods (starting with "validate_")
            if attr_name.startswith('validate_') and isinstance(attr_value, FunctionType):
                field_name = attr_name[9:]  # remove 'validate_' prefix
                mcs.register_validation_rule(name, field_name, attr_value)

            # Find relationship initialization methods
            if attr_name == 'initialize_relationships' and isinstance(attr_value, FunctionType):
                mcs.register_relationship_initializer(name, attr_value.__get__(None, cls))

        return cls

    def __init__(cls, name: str, bases: tuple, attrs: Dict[str, Any]) -> None:
        """
        Custom metaclass __init__ method for additional class initialization.

        Args:
            name: Name of the class being created
            bases: Base classes
            attrs: Class attributes
        """
        super().__init__(name, bases, attrs)

        # Add any additional class initialization here
        if name not in ['BaseModel', 'Base', 'DeclarativeBase'] and not attrs.get('__abstract__', False):
            # Import modules and track dependencies
            module_name = cls.__module__

            # Track in dependency graph
            if module_name not in cls._dependency_graph:
                cls._dependency_graph[module_name] = set()

            for base in bases:
                if hasattr(base, '__module__') and base.__module__ != module_name:
                    cls._dependency_graph[module_name].add(base.__module__)

    def __subclasshook__(cls, subclass: Type) -> Optional[bool]:
        """
        Enhanced subclass hook for interface-like behavior.

        Args:
            subclass: The class to check for interface compliance

        Returns:
            Indication of interface compliance
        """
        # Define required methods for compliance
        required_methods = getattr(cls, '_required_methods', [])

        if required_methods:
            # Check if all required methods are implemented
            return all(
                any(method in B.__dict__ for B in subclass.__mro__)
                for method in required_methods
            )

        return NotImplemented


# Export for convenience
__all__ = [
    'BaseModelMetaclass',
    'ModelRegistryMixin',
    'ModelValidationMixin',
    'ModelRelationshipMixin'
]