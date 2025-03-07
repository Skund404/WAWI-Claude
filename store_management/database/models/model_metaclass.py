# database/models/model_metaclass.py
"""
Comprehensive Model Metaclass for Leatherworking Management System

This module defines the metaclass used for all SQLAlchemy models in the application,
providing automatic model registration, validation capabilities, and relationship management.
"""

import logging
from typing import Any, Dict, Type, Optional, List, Set, ClassVar, Tuple, Union, Callable
import datetime

# Setup logger
logger = logging.getLogger(__name__)


class BaseModelMetaclass(type):
    """
    Metaclass for SQLAlchemy models that provides automatic registration,
    validation capabilities, and relationship management.

    This metaclass tracks all model classes and provides utilities for:
    - Model registration and discovery
    - Validation rule management
    - Relationship initialization and management
    """
    # Class variables for tracking models and their metadata
    _registered_models: Dict[str, Type] = {}
    _model_metadata: Dict[str, Dict[str, Any]] = {}
    _validation_rules: Dict[str, Dict[str, Callable]] = {}
    _relationship_initializers: Dict[str, List[Callable]] = {}
    _deferred_relationships: Dict[str, Dict[str, Any]] = {}
    _dependency_graph: Dict[str, Set[str]] = {}

    def __new__(mcs, name, bases, attrs):
        """
        Create a new model class and register it if not abstract.

        Args:
            name: Name of the class
            bases: Base classes
            attrs: Class attributes

        Returns:
            Newly created class
        """
        # Create the new class
        cls = super().__new__(mcs, name, bases, attrs)

        # Register the model if it's not abstract
        if name != 'Base' and not attrs.get('__abstract__', False) and hasattr(cls, '__tablename__'):
            mcs._registered_models[name] = cls
            mcs._model_metadata[name] = {
                'module': cls.__module__,
                'tablename': getattr(cls, '__tablename__', None),
                'registration_time': datetime.datetime.utcnow()
            }
            logger.debug(f"Registered model: {name} from {cls.__module__}")

        return cls

    @classmethod
    def register_model(mcs, model_class: Type, model_name: Optional[str] = None) -> None:
        """
        Register a model class in the central registry.

        Args:
            model_class: The model class to register
            model_name: Optional custom name for the model (defaults to class name)
        """
        name = model_name or model_class.__name__
        mcs._registered_models[name] = model_class

        # Store metadata about the model
        mcs._model_metadata[name] = {
            'module': model_class.__module__,
            'tablename': getattr(model_class, '__tablename__', None),
            'registration_time': datetime.datetime.utcnow()
        }

        logger.debug(f"Registered model: {name} from {model_class.__module__}")

    @classmethod
    def get_model(mcs, model_name: str) -> Optional[Type]:
        """
        Retrieve a registered model by name.

        Args:
            model_name: Name of the model to retrieve

        Returns:
            The model class or None if not found
        """
        return mcs._registered_models.get(model_name)

    @classmethod
    def list_registered_models(mcs) -> List[str]:
        """
        Get a list of all registered model names.

        Returns:
            List of registered model names
        """
        return list(mcs._registered_models.keys())

    @classmethod
    def get_model_metadata(mcs, model_name: str) -> Dict[str, Any]:
        """
        Get metadata for a specific model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary of model metadata
        """
        return mcs._model_metadata.get(model_name, {})

    @classmethod
    def register_validation_rule(mcs, model_name: str, field_name: str, rule: Callable) -> None:
        """
        Register a validation rule for a specific model field.

        Args:
            model_name: Name of the model
            field_name: Name of the field to validate
            rule: Validation function taking the field value and returning a bool or error message
        """
        if model_name not in mcs._validation_rules:
            mcs._validation_rules[model_name] = {}

        mcs._validation_rules[model_name][field_name] = rule
        logger.debug(f"Registered validation rule for {model_name}.{field_name}")

    @classmethod
    def get_validation_rules(mcs, model_name: str) -> Dict[str, Callable]:
        """
        Get all validation rules for a model.

        Args:
            model_name: Name of the model

        Returns:
            Dictionary mapping field names to validation functions
        """
        return mcs._validation_rules.get(model_name, {})

    @classmethod
    def validate_model_data(mcs, model_name: str, data: Dict[str, Any]) -> Tuple[bool, Dict[str, List[str]]]:
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

        for field, rule in mcs.get_validation_rules(model_name).items():
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

    @classmethod
    def register_relationship_initializer(mcs, model_name: str, initializer: Callable) -> None:
        """
        Register a function to initialize relationships for a model.

        Args:
            model_name: Name of the model
            initializer: Function that initializes relationships
        """
        if model_name not in mcs._relationship_initializers:
            mcs._relationship_initializers[model_name] = []

        mcs._relationship_initializers[model_name].append(initializer)
        logger.debug(f"Registered relationship initializer for {model_name}")

    @classmethod
    def initialize_relationships(mcs, model_name: str) -> None:
        """
        Execute all registered relationship initializers for a model.

        Args:
            model_name: Name of the model
        """
        initializers = mcs._relationship_initializers.get(model_name, [])
        for initializer in initializers:
            try:
                initializer()
                logger.debug(f"Initialized relationships for {model_name}")
            except Exception as e:
                logger.error(f"Error initializing relationships for {model_name}: {e}")

    @classmethod
    def initialize_all_relationships(mcs) -> None:
        """
        Initialize relationships for all registered models.
        """
        for model_name in mcs._relationship_initializers:
            mcs.initialize_relationships(model_name)

        # Process any deferred relationships
        mcs._process_deferred_relationships()

        logger.info("Initialized all model relationships")

    @classmethod
    def defer_relationship(mcs, model_name: str, relationship_name: str, target_model: str) -> None:
        """
        Defer a relationship that needs to be resolved later.

        Args:
            model_name: Source model name
            relationship_name: Name of the relationship to establish
            target_model: Target model name
        """
        if model_name not in mcs._deferred_relationships:
            mcs._deferred_relationships[model_name] = {}

        mcs._deferred_relationships[model_name][relationship_name] = target_model
        logger.debug(f"Deferred relationship: {model_name}.{relationship_name} -> {target_model}")

    @classmethod
    def _process_deferred_relationships(mcs) -> None:
        """
        Process all deferred relationships after all models are registered.
        """
        try:
            for model_name, relationships in mcs._deferred_relationships.items():
                model_class = mcs.get_model(model_name)
                if not model_class:
                    logger.warning(f"Cannot resolve deferred relationships - model {model_name} not found")
                    continue

                for rel_name, target_model in relationships.items():
                    target_class = mcs.get_model(target_model)
                    if not target_class:
                        logger.warning(f"Cannot resolve deferred relationship - target {target_model} not found")
                        continue

                    # Create the relationship dynamically
                    # In practice, this would involve setting up SQLAlchemy relationships
                    logger.debug(f"Resolved deferred relationship: {model_name}.{rel_name} -> {target_model}")
        except Exception as e:
            logger.error(f"Error processing deferred relationships: {e}")


# For backward compatibility
ModelRegistryMixin = BaseModelMetaclass
ModelValidationMixin = BaseModelMetaclass
ModelRelationshipMixin = BaseModelMetaclass

__all__ = [
    'BaseModelMetaclass',
    'ModelRegistryMixin',
    'ModelValidationMixin',
    'ModelRelationshipMixin'
]