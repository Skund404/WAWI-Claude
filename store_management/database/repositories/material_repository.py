# Path: database/repositories/material_repository.py
"""Material Repository for managing material-related database operations."""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_, func

from database.repositories.base_repository import BaseRepository
from database.models.material import Material
from database.models.enums import MaterialType


class MaterialRepository(BaseRepository):
    """
    Repository for managing material-related database operations.

    Provides methods for CRUD operations and complex queries on materials.
    """

    def __init__(self, session: Session):
        """
        Initialize the Material Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Material)
        self._logger = logging.getLogger(__name__)

    def create(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material.

        Args:
            material_data (Dict[str, Any]): Data for the new material

        Returns:
            Material: Created material instance
        """
        try:
            # Validate and prepare material data
            if 'type' in material_data and isinstance(material_data['type'], str):
                try:
                    material_data['type'] = MaterialType[material_data['type']]
                except (KeyError, ValueError):
                    self._logger.warning(f"Invalid material type: {material_data['type']}")
                    material_data['type'] = MaterialType.OTHER

            material = Material(**material_data)
            self._session.add(material)
            self._session.commit()
            return material
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error creating material: {str(e)}")
            raise

    def list(
            self,
            filter_criteria: Optional[Dict[str, Any]] = None,
            sort_by: Optional[str] = None,
            limit: Optional[int] = None
    ) -> List[Material]:
        """
        List materials with optional filtering and sorting.

        Args:
            filter_criteria (Optional[Dict[str, Any]], optional): Filters to apply
            sort_by (Optional[str], optional): Field to sort by
            limit (Optional[int], optional): Maximum number of results

        Returns:
            List[Material]: List of material objects
        """
        try:
            # Start with base query
            query = self._session.query(Material)

            # Apply filtering
            if filter_criteria:
                for key, value in filter_criteria.items():
                    if key == 'type' and isinstance(value, str):
                        # Convert string to enum if needed
                        try:
                            value = MaterialType[value]
                        except (KeyError, ValueError):
                            self._logger.warning(f"Invalid material type: {value}")
                            continue

                    # Handle complex filter conditions
                    if isinstance(value, dict):
                        for op, val in value.items():
                            if op == '$lt':
                                query = query.filter(getattr(Material, key) < val)
                            elif op == '$gt':
                                query = query.filter(getattr(Material, key) > val)
                            elif op == '$lte':
                                query = query.filter(getattr(Material, key) <= val)
                            elif op == '$gte':
                                query = query.filter(getattr(Material, key) >= val)
                    else:
                        query = query.filter(getattr(Material, key) == value)

            # Apply sorting
            if sort_by:
                query = query.order_by(getattr(Material, sort_by))

            # Apply limit
            if limit:
                query = query.limit(limit)

            # Execute and return results
            return query.all()
        except SQLAlchemyError as e:
            self._logger.error(f"Error listing materials: {str(e)}")
            return []

    def update(self, material_id: int, update_data: Dict[str, Any]) -> Material:
        """
        Update an existing material.

        Args:
            material_id (int): ID of the material to update
            update_data (Dict[str, Any]): Data to update

        Returns:
            Material: Updated material instance
        """
        try:
            # Find the material
            material = self._session.query(Material).filter(Material.id == material_id).first()

            if not material:
                raise ValueError(f"Material with ID {material_id} not found")

            # Handle type conversion if needed
            if 'type' in update_data and isinstance(update_data['type'], str):
                try:
                    update_data['type'] = MaterialType[update_data['type']]
                except (KeyError, ValueError):
                    self._logger.warning(f"Invalid material type: {update_data['type']}")
                    update_data['type'] = MaterialType.OTHER

            # Update material attributes
            for key, value in update_data.items():
                setattr(material, key, value)

            # Commit changes
            self._session.commit()
            return material
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error updating material {material_id}: {str(e)}")
            raise

    def delete(self, material_id: int) -> None:
        """
        Delete a material from the system.

        Args:
            material_id (int): ID of the material to delete
        """
        try:
            # Find the material
            material = self._session.query(Material).filter(Material.id == material_id).first()

            if not material:
                raise ValueError(f"Material with ID {material_id} not found")

            # Delete material
            self._session.delete(material)
            self._session.commit()
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Error deleting material {material_id}: {str(e)}")
            raise