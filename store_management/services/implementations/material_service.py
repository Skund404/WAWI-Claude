# database/services/implementations/material_service.py
"""
Service implementation for managing Material entities and their relationships.
"""

from typing import Any, Dict, List, Optional, Union
import uuid
import logging

from database.models.enums import (
    MaterialType,
    MaterialQualityGrade,
    InventoryStatus,
    TransactionType
)
from database.models.material import Material
from database.models.transaction import MaterialTransaction
from database.models.material_inventory import MaterialInventory
from database.repositories.material_repository import MaterialRepository
from database.repositories.material_inventory_repository import MaterialInventoryRepository
from database.repositories.transaction_repository import TransactionRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.material_service import IMaterialService


class MaterialService(BaseService[Material], IMaterialService):
    """
    Service for managing Material-related operations.

    Handles creation, retrieval, updating, and deletion of materials,
    along with inventory and transaction management.
    """

    def __init__(
            self,
            session=None,
            material_repository: Optional[MaterialRepository] = None,
            material_inventory_repository: Optional[MaterialInventoryRepository] = None,
            transaction_repository: Optional[TransactionRepository] = None
    ):
        """
        Initialize the Material Service.

        Args:
            session: SQLAlchemy database session
            material_repository: Repository for material data access
            material_inventory_repository: Repository for material inventory
            transaction_repository: Repository for material transactions
        """
        self.session = session or get_db_session()
        self.material_repository = material_repository or MaterialRepository(self.session)
        self.material_inventory_repository = (
                material_inventory_repository or
                MaterialInventoryRepository(self.session)
        )
        self.transaction_repository = (
                transaction_repository or
                TransactionRepository(self.session)
        )
        self.logger = logging.getLogger(__name__)

    def create_material(
            self,
            name: str,
            material_type: MaterialType,
            quality_grade: MaterialQualityGrade,
            supplier_id: Optional[str] = None,
            **kwargs
    ) -> Material:
        """
        Create a new material.

        Args:
            name: Material name
            material_type: Type of material
            quality_grade: Quality grade of the material
            supplier_id: Optional supplier identifier
            **kwargs: Additional material attributes

        Returns:
            Created Material instance

        Raises:
            ValidationError: If material creation fails validation
        """
        try:
            # Validate required fields
            if not name or not material_type or not quality_grade:
                raise ValidationError("Missing required material attributes")

            # Generate a unique identifier
            material_id = str(uuid.uuid4())

            # Create material
            material_data = {
                'id': material_id,
                'name': name,
                'type': material_type,
                'quality': quality_grade,
                'supplier_id': supplier_id,
                **kwargs
            }

            material = Material(**material_data)

            # Save material
            with self.session:
                self.session.add(material)
                self.session.commit()
                self.session.refresh(material)

            self.logger.info(f"Created material: {material.name}")
            return material

        except Exception as e:
            self.logger.error(f"Error creating material: {str(e)}")
            raise ValidationError(f"Material creation failed: {str(e)}")

    def get_material_by_id(self, material_id: str) -> Material:
        """
        Retrieve a material by its ID.

        Args:
            material_id: Unique identifier of the material

        Returns:
            Material instance

        Raises:
            NotFoundError: If material is not found
        """
        try:
            material = self.material_repository.get(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")
            return material
        except Exception as e:
            self.logger.error(f"Error retrieving material: {str(e)}")
            raise NotFoundError(f"Material retrieval failed: {str(e)}")

    def update_material(
            self,
            material_id: str,
            **update_data: Dict[str, Any]
    ) -> Material:
        """
        Update an existing material.

        Args:
            material_id: Unique identifier of the material
            update_data: Dictionary of fields to update

        Returns:
            Updated Material instance

        Raises:
            NotFoundError: If material is not found
            ValidationError: If update fails validation
        """
        try:
            # Retrieve existing material
            material = self.get_material_by_id(material_id)

            # Validate update data
            if 'type' in update_data and not isinstance(update_data['type'], MaterialType):
                raise ValidationError("Invalid material type")

            if 'quality' in update_data and not isinstance(update_data['quality'], MaterialQualityGrade):
                raise ValidationError("Invalid material quality grade")

            # Update material attributes
            for key, value in update_data.items():
                setattr(material, key, value)

            # Save updates
            with self.session:
                self.session.add(material)
                self.session.commit()
                self.session.refresh(material)

            self.logger.info(f"Updated material: {material.name}")
            return material

        except Exception as e:
            self.logger.error(f"Error updating material: {str(e)}")
            raise ValidationError(f"Material update failed: {str(e)}")

    def delete_material(self, material_id: str) -> bool:
        """
        Delete a material.

        Args:
            material_id: Unique identifier of the material

        Returns:
            Boolean indicating successful deletion

        Raises:
            NotFoundError: If material is not found
        """
        try:
            # Retrieve material
            material = self.get_material_by_id(material_id)

            # Delete material
            with self.session:
                self.session.delete(material)
                self.session.commit()

            self.logger.info(f"Deleted material: {material_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error deleting material: {str(e)}")
            raise NotFoundError(f"Material deletion failed: {str(e)}")

    def get_materials_by_type(
            self,
            material_type: Optional[MaterialType] = None,
            quality_grade: Optional[MaterialQualityGrade] = None
    ) -> List[Material]:
        """
        Retrieve materials filtered by type and quality grade.

        Args:
            material_type: Optional material type to filter materials
            quality_grade: Optional quality grade to filter materials

        Returns:
            List of Material instances
        """
        try:
            # Use repository method to filter materials
            materials = self.material_repository.get_by_type_and_quality(
                material_type,
                quality_grade
            )
            return materials
        except Exception as e:
            self.logger.error(f"Error retrieving materials: {str(e)}")
            return []

    def add_material_inventory(
            self,
            material_id: str,
            quantity: float,
            storage_location: Optional[str] = None,
            inventory_status: InventoryStatus = InventoryStatus.IN_STOCK
    ) -> MaterialInventory:
        """
        Add inventory for a specific material.

        Args:
            material_id: Unique identifier of the material
            quantity: Quantity to add to inventory
            storage_location: Optional storage location
            inventory_status: Inventory status (default: IN_STOCK)

        Returns:
            MaterialInventory instance

        Raises:
            NotFoundError: If material is not found
            ValidationError: If inventory addition fails
        """
        try:
            # Verify material exists
            material = self.get_material_by_id(material_id)

            # Create inventory entry
            inventory_data = {
                'material_id': material_id,
                'quantity': quantity,
                'storage_location': storage_location,
                'status': inventory_status
            }

            material_inventory = MaterialInventory(**inventory_data)

            # Save inventory
            with self.session:
                self.session.add(material_inventory)
                self.session.commit()
                self.session.refresh(material_inventory)

            self.logger.info(f"Added inventory for material: {material_id}")
            return material_inventory

        except Exception as e:
            self.logger.error(f"Error adding material inventory: {str(e)}")
            raise ValidationError(f"Material inventory addition failed: {str(e)}")

    def record_material_transaction(
            self,
            material_id: str,
            quantity: float,
            transaction_type: TransactionType,
            description: Optional[str] = None,
            related_entity_id: Optional[str] = None
    ) -> MaterialTransaction:
        """
        Record a transaction for a material.

        Args:
            material_id: Unique identifier of the material
            quantity: Transaction quantity
            transaction_type: Type of transaction
            description: Optional transaction description
            related_entity_id: Optional ID of related entity (e.g., purchase, project)

        Returns:
            MaterialTransaction instance

        Raises:
            NotFoundError: If material is not found
            ValidationError: If transaction recording fails
        """
        try:
            # Verify material exists
            material = self.get_material_by_id(material_id)

            # Create transaction
            transaction_data = {
                'material_id': material_id,
                'quantity': quantity,
                'transaction_type': transaction_type,
                'description': description,
                'related_entity_id': related_entity_id
            }

            material_transaction = MaterialTransaction(**transaction_data)

            # Save transaction
            with self.session:
                self.session.add(material_transaction)

                # Update inventory based on transaction type
                inventory = self.material_inventory_repository.get_by_material_id(material_id)
                if inventory:
                    if transaction_type in [TransactionType.PURCHASE, TransactionType.RETURN]:
                        inventory.quantity += quantity
                    elif transaction_type in [TransactionType.USAGE, TransactionType.WASTE]:
                        inventory.quantity -= quantity

                    self.session.add(inventory)

                self.session.commit()
                self.session.refresh(material_transaction)

            self.logger.info(f"Recorded material transaction: {transaction_type} for material {material_id}")
            return material_transaction

        except Exception as e:
            self.logger.error(f"Error recording material transaction: {str(e)}")
            raise ValidationError(f"Material transaction recording failed: {str(e)}")