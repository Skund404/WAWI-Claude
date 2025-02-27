#!/usr/bin/env python3
# Path: store_management/services/implementations/material_service.py
"""
Material Service Implementation Module

Provides concrete implementation of the MaterialService interface.
"""

import logging
from typing import Dict, Any, Optional, List

from database.models import Part
from database.sqlalchemy.session import get_db_session
from services.interfaces import MaterialService
from utils.logger import get_logger


class MaterialServiceImpl(MaterialService):
    """
    Concrete implementation of the MaterialService interface.

    Provides methods for managing materials with database interaction.
    """

    def __init__(self):
        """
        Initialize the Material Service with logging.
        """
        self.logger = get_logger(__name__)

    def validate_model_creation(
        self,
        model_name: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate data before model creation.

        Args:
            model_name (str): Name of the model being created.
            data (Dict[str, Any]): Data to be validated.

        Returns:
            Dict[str, Any]: Validated and potentially modified data.

        Raises:
            ValueError: If data validation fails.
        """
        # Basic validation for Part model
        if model_name == 'Part':
            # Ensure name is provided and not empty
            if not data.get('name'):
                raise ValueError("Part name is required")

            # Validate quantity
            quantity = data.get('quantity', 0.0)
            if not isinstance(quantity, (int, float)) or quantity < 0:
                raise ValueError("Quantity must be a non-negative number")

            # Ensure unit is provided
            data['unit'] = data.get('unit', 'unit')

            # Set default values
            data['is_active'] = data.get('is_active', True)

        return data

    def get_material_by_name(self, name: str) -> Optional[Part]:
        """
        Retrieve a material by its name.

        Args:
            name (str): Name of the material to retrieve.

        Returns:
            Optional[Part]: The material if found, None otherwise.
        """
        try:
            with get_db_session() as session:
                material = session.query(Part).filter_by(name=name).first()
                return material
        except Exception as e:
            self.logger.error(f"Error retrieving material by name {name}: {e}")
            return None

    def create_material(
        self,
        name: str,
        **kwargs
    ) -> Part:
        """
        Create a new material.

        Args:
            name (str): Name of the material.
            **kwargs: Additional material attributes.

        Returns:
            Part: The newly created material.

        Raises:
            ValueError: If material creation fails validation.
        """
        try:
            # Validate the material data
            validated_data = self.validate_model_creation(
                'Part', {'name': name, **kwargs})

            # Check if material already exists
            existing_material = self.get_material_by_name(name)
            if existing_material:
                raise ValueError(f"Material with name '{name}' already exists")

            # Create the new material
            with get_db_session() as session:
                new_material = Part(**validated_data)
                session.add(new_material)
                session.commit()
                session.refresh(new_material)
                return new_material

        except Exception as e:
            self.logger.error(f"Error creating material {name}: {e}")
            raise

    def update_material(
        self,
        material: Part,
        **kwargs
    ) -> Part:
        """
        Update an existing material.

        Args:
            material (Part): The material to update.
            **kwargs: Attributes to update.

        Returns:
            Part: The updated material.

        Raises:
            ValueError: If material update fails validation.
        """
        try:
            # Validate the update data
            validated_data = self.validate_model_creation('Part', kwargs)

            # Update the material
            with get_db_session() as session:
                # Update each attribute
                for key, value in validated_data.items():
                    setattr(material, key, value)

                session.add(material)
                session.commit()
                session.refresh(material)
                return material

        except Exception as e:
            self.logger.error(f"Error updating material {material.name}: {e}")
            raise

    def list_materials(
        self,
        filter_criteria: Optional[Dict[str, Any]] = None
    ) -> List[Part]:
        """
        List materials with optional filtering.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional):
                Filtering parameters. Defaults to None.

        Returns:
            List[Part]: List of materials matching the criteria.
        """
        try:
            with get_db_session() as session:
                query = session.query(Part)

                # Apply filters if provided
                if filter_criteria:
                    for key, value in filter_criteria.items():
                        if hasattr(Part, key):
                            query = query.filter(getattr(Part, key) == value)

                return query.all()

        except Exception as e:
            self.logger.error(f"Error listing materials: {e}")
            return []

    def delete_material(self, material: Part) -> bool:
        """
        Delete a material.

        Args:
            material (Part): The material to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        try:
            with get_db_session() as session:
                session.delete(material)
                session.commit()
                return True

        except Exception as e:
            self.logger.error(f"Error deleting material {material.name}: {e}")
            return False

    def validate_material_quantity(
        self,
        material: Part,
        quantity: float
    ) -> bool:
        """
        Validate if a given quantity is valid for a material.

        Args:
            material (Part): The material to validate.
            quantity (float): Quantity to check.

        Returns:
            bool: True if the quantity is valid, False otherwise.
        """
        # Check if material is active
        if not material.is_active:
            return False

        # Check if requested quantity is non-negative
        if quantity < 0:
            return False

        # Optional: Add more complex validation logic
        # For example, checking against maximum inventory capacity
        return True