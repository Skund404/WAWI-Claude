# services/implementations/material_service.py
from database.models.enums import InventoryStatus, MaterialType
from database.models.material import Material
from database.models.base import ModelValidationError
from database.repositories.material_repository import MaterialRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError, ServiceError
from services.interfaces.material_service import IMaterialService

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from typing import Any, Dict, List, Optional
from utils.logger import log_debug, log_error, log_info


class MaterialService(BaseService[Material], IMaterialService):
    """Service for material-related operations."""

    def __init__(self, session: Session):
        """Initialize the Material Service.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__()
        self.session = session
        self.repository = MaterialRepository(session)

    def get_all_materials(self) -> List[Dict[str, Any]]:
        """Get all active materials.

        Returns:
            List of material dictionaries

        Raises:
            ServiceError: If a service error occurs
        """
        try:
            materials = self.repository.get_all()
            return [self.to_dict(material) for material in materials]
        except Exception as e:
            log_error(f"Error retrieving all materials: {str(e)}")
            raise ServiceError(f"Failed to retrieve materials: {str(e)}")

    def get_material_by_id(self, material_id: int) -> Dict[str, Any]:
        """Get material by ID.

        Args:
            material_id: ID of the material

        Returns:
            Material dictionary

        Raises:
            NotFoundError: If material is not found
            ServiceError: If a service error occurs
        """
        try:
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")
            return self.to_dict(material)
        except NotFoundError:
            # Re-raise not found error
            raise
        except Exception as e:
            log_error(f"Error retrieving material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve material: {str(e)}")

    def create_material(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Material creation data

        Returns:
            Created material dictionary

        Raises:
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            # Validate required fields
            self.validate_input(material_data, ['name', 'material_type'])

            # Create material using repository (model validation happens in the model)
            material = self.repository.create(material_data)

            log_info(f"Created material: {material.name}")
            return self.to_dict(material)
        except ModelValidationError as e:
            # Convert model validation error to service validation error
            raise ValidationError(str(e))
        except ValidationError:
            # Re-raise validation error
            raise
        except Exception as e:
            log_error(f"Error creating material: {str(e)}")
            raise ServiceError(f"Failed to create material: {str(e)}")

    def update_material(self, material_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing material.

        Args:
            material_id: ID of the material to update
            update_data: Material update data

        Returns:
            Updated material dictionary

        Raises:
            NotFoundError: If material is not found
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            # Update using repository (model validation happens in the model)
            material = self.repository.update(material_id, update_data)

            log_info(f"Updated material {material_id}")
            return self.to_dict(material)
        except ModelValidationError as e:
            # Convert model validation error to service validation error
            raise ValidationError(str(e))
        except NotFoundError:
            # Re-raise not found error
            raise
        except Exception as e:
            log_error(f"Error updating material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to update material: {str(e)}")

    def delete_material(self, material_id: int) -> bool:
        """Soft delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            True if successful

        Raises:
            NotFoundError: If material is not found
            ServiceError: If a service error occurs
        """
        try:
            success = self.repository.delete(material_id)
            if not success:
                raise NotFoundError(f"Material with ID {material_id} not found")

            log_info(f"Deleted material {material_id}")
            return True
        except NotFoundError:
            # Re-raise not found error
            raise
        except Exception as e:
            log_error(f"Error deleting material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to delete material: {str(e)}")

    def find_materials_by_type(self, material_type: MaterialType) -> List[Dict[str, Any]]:
        """Find materials by type.

        Args:
            material_type: Material type enum value

        Returns:
            List of matching material dictionaries

        Raises:
            ServiceError: If a service error occurs
        """
        try:
            materials = self.repository.find_by_type(material_type)
            return [self.to_dict(material) for material in materials]
        except Exception as e:
            log_error(f"Error finding materials by type {material_type}: {str(e)}")
            raise ServiceError(f"Failed to find materials by type: {str(e)}")

    def adjust_material_quantity(self, material_id: int, quantity_change: float,
                                 notes: Optional[str] = None) -> Dict[str, Any]:
        """Adjust material quantity.

        Args:
            material_id: ID of the material
            quantity_change: Quantity to add (positive) or remove (negative)
            notes: Optional notes about the adjustment

        Returns:
            Updated material dictionary

        Raises:
            NotFoundError: If material is not found
            ValidationError: If validation fails
            ServiceError: If a service error occurs
        """
        try:
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Use the model's adjust_quantity method
            material.adjust_quantity(quantity_change, notes=notes)

            self.session.commit()
            log_info(f"Adjusted material {material_id} quantity by {quantity_change}")

            return self.to_dict(material)
        except NotFoundError:
            # Re-raise not found error
            raise
        except ValueError as e:
            # Convert ValueError to ValidationError
            raise ValidationError(str(e))
        except Exception as e:
            self.session.rollback()
            log_error(f"Error adjusting material quantity: {str(e)}")
            raise ServiceError(f"Failed to adjust material quantity: {str(e)}")