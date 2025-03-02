# services/implementations/material_service.py
"""
Material service implementation for managing material-related operations.
"""

import logging
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.material import Material
from database.models.enums import MaterialType, InventoryStatus
from services.interfaces.material_service import IMaterialService
from services.base_service import BaseService, NotFoundError, ValidationError
from utils.logger import log_error, log_info, log_debug


class MaterialService(BaseService[Material], IMaterialService):
    """
    Service implementation for managing materials.
    """

    def __init__(self, session: Session):
        """
        Initialize the Material Service.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session)
        self.logger = logging.getLogger(__name__)

    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material.

        Args:
            material_data (Dict[str, Any]): Material creation data

        Returns:
            Material: Newly created material instance

        Raises:
            ValidationError: If material data is invalid
        """
        try:
            # Log the attempt to create a material with sanitized data
            log_info(f"Attempting to create material with name: {material_data.get('name', 'N/A')}")
            log_debug(f"Material creation data: {material_data}")

            # Validate input data
            material = Material.create(**material_data)

            # Add to session and commit
            self.session.add(material)
            self.session.commit()

            log_info(f"Material created successfully: {material.name} (ID: {material.id})")
            return material

        except ValueError as ve:
            self.session.rollback()
            log_error(ve, {
                'context': 'Material Creation',
                'input_data': material_data
            })
            raise ValidationError(str(ve))

        except SQLAlchemyError as se:
            self.session.rollback()
            log_error(se, {
                'context': 'Material Database Operation',
                'input_data': material_data
            })
            raise ValidationError(f"Could not create material: {se}")

    def update_material(self, material_id: int, update_data: Dict[str, Any]) -> Material:
        """
        Update an existing material.

        Args:
            material_id (int): ID of the material to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Material: Updated material instance

        Raises:
            NotFoundError: If material is not found
            ValidationError: If update data is invalid
        """
        try:
            # Log the update attempt
            log_info(f"Attempting to update material with ID: {material_id}")
            log_debug(f"Update data: {update_data}")

            # Retrieve existing material
            material = self.session.query(Material).get(material_id)
            if not material:
                log_error(NotFoundError(f"Material with ID {material_id} not found"))
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Update material
            material.update(**update_data)

            # Commit changes
            self.session.commit()

            log_info(f"Material updated successfully: {material.name} (ID: {material.id})")
            return material

        except ValueError as ve:
            self.session.rollback()
            log_error(ve, {
                'context': 'Material Update',
                'material_id': material_id,
                'update_data': update_data
            })
            raise ValidationError(str(ve))

        except SQLAlchemyError as se:
            self.session.rollback()
            log_error(se, {
                'context': 'Material Database Update',
                'material_id': material_id,
                'update_data': update_data
            })
            raise ValidationError(f"Could not update material: {se}")

    def get_material_by_id(self, material_id: int, include_relationships: bool = False) -> Material:
        """
        Retrieve a material by its ID.

        Args:
            material_id (int): ID of the material to retrieve
            include_relationships (bool, optional): Whether to include related data. Defaults to False.

        Returns:
            Material: Retrieved material instance

        Raises:
            NotFoundError: If material is not found
        """
        try:
            log_debug(f"Retrieving material with ID: {material_id}")

            material = self.session.query(Material).get(material_id)
            if not material:
                log_error(NotFoundError(f"Material with ID {material_id} not found"))
                raise NotFoundError(f"Material with ID {material_id} not found")

            log_info(f"Retrieved material: {material.name} (ID: {material.id})")
            return material

        except Exception as e:
            log_error(e, {'context': 'Material Retrieval', 'material_id': material_id})
            raise

    def list_materials(
            self,
            material_type: Optional[MaterialType] = None,
            status: Optional[InventoryStatus] = None,
            limit: int = 100,
            offset: int = 0
    ) -> List[Material]:
        """
        List materials with optional filtering.

        Args:
            material_type (Optional[MaterialType]): Filter by material type
            status (Optional[InventoryStatus]): Filter by inventory status
            limit (int, optional): Maximum number of results. Defaults to 100.
            offset (int, optional): Offset for pagination. Defaults to 0.

        Returns:
            List[Material]: List of materials matching the filter criteria
        """
        try:
            log_debug(f"Listing materials with filters: type={material_type}, status={status}")

            query = self.session.query(Material)

            if material_type:
                query = query.filter(Material.material_type == material_type)

            if status:
                query = query.filter(Material.status == status)

            materials = query.limit(limit).offset(offset).all()

            log_info(f"Retrieved {len(materials)} materials")
            return materials

        except Exception as e:
            log_error(e, {
                'context': 'Material Listing',
                'material_type': material_type,
                'status': status,
                'limit': limit,
                'offset': offset
            })
            raise

    def delete_material(self, material_id: int) -> None:
        """
        Soft delete a material.

        Args:
            material_id (int): ID of the material to delete

        Raises:
            NotFoundError: If material is not found
        """
        try:
            log_info(f"Attempting to soft delete material with ID: {material_id}")

            material = self.session.query(Material).get(material_id)
            if not material:
                log_error(NotFoundError(f"Material with ID {material_id} not found"))
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Perform soft delete
            material.soft_delete()

            self.session.commit()
            log_info(f"Soft deleted material: {material.name} (ID: {material.id})")

        except SQLAlchemyError as se:
            self.session.rollback()
            log_error(se, {
                'context': 'Material Soft Delete',
                'material_id': material_id
            })
            raise ValidationError(f"Could not delete material: {se}")

    def restore_material(self, material_id: int) -> Material:
        """
        Restore a soft-deleted material.

        Args:
            material_id (int): ID of the material to restore

        Returns:
            Material: Restored material instance

        Raises:
            NotFoundError: If material is not found
        """
        try:
            log_info(f"Attempting to restore material with ID: {material_id}")

            material = self.session.query(Material).get(material_id)
            if not material:
                log_error(NotFoundError(f"Material with ID {material_id} not found"))
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Restore the material
            material.restore()

            self.session.commit()
            log_info(f"Restored material: {material.name} (ID: {material.id})")
            return material

        except SQLAlchemyError as se:
            self.session.rollback()
            log_error(se, {
                'context': 'Material Restoration',
                'material_id': material_id
            })
            raise ValidationError(f"Could not restore material: {se}")