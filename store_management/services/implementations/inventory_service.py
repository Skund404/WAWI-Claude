# services/implementations/material_service.py
"""
Implementation of Material Service for the leatherworking store management application.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from services.interfaces.material_service import IMaterialService, MaterialType
from database.models.material import Material
from database.repositories.material_repository import MaterialRepository
from utils.error_handler import ValidationError, NotFoundError


class MaterialServiceImpl(IMaterialService):
    """
    Concrete implementation of the Material Service interface.

    Manages CRUD operations and business logic for materials in the leatherworking store.
    """

    def __init__(self, session: Session):
        """
        Initialize the Material Service with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self.session = session
        self.repository = MaterialRepository(session)
        self.logger = logging.getLogger(__name__)

    def _validate_material_data(self, material_data: Dict[str, Any]) -> None:
        """
        Validate material data before creation or update.

        Args:
            material_data (Dict[str, Any]): Material data to validate

        Raises:
            ValidationError: If material data is invalid
        """
        required_fields = ['name', 'material_type', 'quantity']
        for field in required_fields:
            if field not in material_data or not material_data[field]:
                raise ValidationError(f"Missing required field: {field}")

        # Validate material type
        try:
            MaterialType(material_data['material_type'])
        except ValueError:
            raise ValidationError(f"Invalid material type: {material_data['material_type']}")

    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material entry.

        Args:
            material_data (Dict[str, Any]): Data for the new material

        Returns:
            Material: Created material object

        Raises:
            ValidationError: If material data is invalid
        """
        try:
            # Validate input data
            self._validate_material_data(material_data)

            # Create material
            material = Material(**material_data)

            # Save to database
            with self.session.begin():
                self.repository.create(material)

            self.logger.info(f"Created material: {material.name}")
            return material

        except ValidationError as ve:
            self.logger.error(f"Validation error creating material: {ve}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error creating material: {e}")
            raise ValidationError(f"Could not create material: {str(e)}")

    def get_material(self, material_id: str) -> Optional[Material]:
        """
        Retrieve a material by its identifier.

        Args:
            material_id (str): Unique identifier for the material

        Returns:
            Optional[Material]: Material object or None if not found

        Raises:
            NotFoundError: If material is not found
        """
        try:
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")
            return material
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving material {material_id}: {e}")
            raise NotFoundError(f"Could not retrieve material: {str(e)}")

    def update_material(self, material_id: str, update_data: Dict[str, Any]) -> Material:
        """
        Update an existing material.

        Args:
            material_id (str): Unique identifier for the material
            update_data (Dict[str, Any]): Data to update

        Returns:
            Material: Updated material object

        Raises:
            ValidationError: If update data is invalid
            NotFoundError: If material is not found
        """
        try:
            # Validate material exists
            material = self.get_material(material_id)

            # Validate update data
            if 'material_type' in update_data:
                MaterialType(update_data['material_type'])

            # Update material
            for key, value in update_data.items():
                setattr(material, key, value)

            # Save updates
            with self.session.begin():
                self.repository.update(material)

            self.logger.info(f"Updated material: {material_id}")
            return material

        except (ValidationError, NotFoundError) as e:
            self.logger.error(f"Error updating material {material_id}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error updating material {material_id}: {e}")
            raise ValidationError(f"Could not update material: {str(e)}")

    def delete_material(self, material_id: str) -> bool:
        """
        Delete a material by its identifier.

        Args:
            material_id (str): Unique identifier for the material

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If material is not found
        """
        try:
            # Validate material exists
            material = self.get_material(material_id)

            # Delete material
            with self.session.begin():
                self.repository.delete(material)

            self.logger.info(f"Deleted material: {material_id}")
            return True

        except (ValidationError, NotFoundError) as e:
            self.logger.error(f"Error deleting material {material_id}: {e}")
            raise
        except SQLAlchemyError as e:
            self.logger.error(f"Database error deleting material {material_id}: {e}")
            raise ValidationError(f"Could not delete material: {str(e)}")

    def list_materials(self,
                       material_type: Optional[MaterialType] = None,
                       page: int = 1,
                       page_size: int = 10) -> List[Material]:
        """
        List materials with optional filtering and pagination.

        Args:
            material_type (Optional[MaterialType], optional): Filter by material type
            page (int, optional): Page number for pagination. Defaults to 1.
            page_size (int, optional): Number of items per page. Defaults to 10.

        Returns:
            List[Material]: List of material objects
        """
        try:
            # Build query conditions
            conditions = {}
            if material_type:
                conditions['material_type'] = material_type.value

            # Calculate offset
            offset = (page - 1) * page_size

            # Retrieve materials
            materials = self.repository.list_with_filters(
                conditions,
                limit=page_size,
                offset=offset
            )

            self.logger.info(f"Listed materials: type={material_type}, page={page}")
            return materials

        except SQLAlchemyError as e:
            self.logger.error(f"Error listing materials: {e}")
            raise ValidationError(f"Could not list materials: {str(e)}")