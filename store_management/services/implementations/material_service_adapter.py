# services/implementations/material_service_adapter.py
"""
Material Service Adapter to bridge the new metaclass model structure
with existing service interfaces.
"""

import logging
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from sqlalchemy.exc import SQLAlchemyError

from database.models.material import Material
from database.models.material import MaterialTransaction
from database.models.enums import MaterialType, MaterialQualityGrade, InventoryStatus, TransactionType
from database.repositories.material_repository import MaterialRepository
from services.base_service import BaseService, NotFoundError, ValidationError, ServiceError
from services.interfaces.material_service import IMaterialService
from utils.validators import DataSanitizer


class MaterialServiceAdapter(BaseService, IMaterialService):
    """
    Material Service implementation that adapts to the new metaclass-based
    model structure while maintaining compatibility with existing interfaces.
    """

    def __init__(self, session: Session):
        """Initialize the Material Service Adapter.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__()
        self._session = session
        self._repository = MaterialRepository(session)
        self._logger = logging.getLogger(__name__)
        self._sanitizer = DataSanitizer()

    def _validate_material_data(self, material_data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
        """
        Validate and sanitize material data.

        Args:
            material_data (Dict[str, Any]): Material data to validate
            is_update (bool, optional): Whether this is an update operation. Defaults to False.

        Returns:
            Dict[str, Any]: Sanitized and validated material data

        Raises:
            ValidationError: If validation fails
        """
        # Remove any None or empty string values
        sanitized_data = {k: v for k, v in material_data.items() if v is not None and v != ''}

        # Validate required fields for creation
        if not is_update:
            required_fields = ["name", "material_type"]
            for field in required_fields:
                if field not in sanitized_data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate material type
        if "material_type" in sanitized_data:
            try:
                MaterialType(sanitized_data["material_type"])
            except ValueError:
                raise ValidationError(f"Invalid material type: {sanitized_data['material_type']}")

        # Validate quality grade if provided
        if "quality_grade" in sanitized_data:
            try:
                MaterialQualityGrade(sanitized_data["quality_grade"])
            except ValueError:
                raise ValidationError(f"Invalid quality grade: {sanitized_data['quality_grade']}")

        # Validate quantity if provided
        if "quantity" in sanitized_data:
            try:
                quantity = float(sanitized_data["quantity"])
                if quantity < 0:
                    raise ValidationError("Quantity cannot be negative")
                sanitized_data["quantity"] = quantity
            except ValueError:
                raise ValidationError("Quantity must be a valid number")

        # Validate price if provided
        if "price" in sanitized_data:
            try:
                price = float(sanitized_data["price"])
                if price < 0:
                    raise ValidationError("Price cannot be negative")
                sanitized_data["price"] = price
            except ValueError:
                raise ValidationError("Price must be a valid number")

        return sanitized_data

    def _material_to_dict(self, material: Material) -> Dict[str, Any]:
        """
        Convert Material model to dictionary representation.

        Args:
            material (Material): Material model instance

        Returns:
            Dict[str, Any]: Dictionary representation of the material
        """
        material_dict = {
            "id": material.id,
            "uuid": material.uuid,
            "name": material.name,
            "material_type": material.material_type,
            "quantity": material.quantity,
            "description": getattr(material, 'description', ''),
            "price": getattr(material, 'price', None),
            "status": material.status,
            "created_at": material.created_at,
            "updated_at": material.updated_at
        }

        # Add optional fields if they exist
        optional_fields = [
            'leather_type', 'quality_grade', 'area',
            'color', 'thickness', 'supplier_id'
        ]
        for field in optional_fields:
            if hasattr(material, field):
                value = getattr(material, field)
                if value is not None:
                    material_dict[field] = value

        return material_dict

    def _transaction_to_dict(self, transaction: MaterialTransaction) -> Dict[str, Any]:
        """
        Convert MaterialTransaction model to dictionary representation.

        Args:
            transaction (MaterialTransaction): MaterialTransaction model instance

        Returns:
            Dict[str, Any]: Dictionary representation of the transaction
        """
        return {
            "id": transaction.id,
            "material_id": transaction.material_id,
            "transaction_type": transaction.transaction_type,
            "quantity": transaction.quantity,
            "notes": transaction.notes or '',
            "created_at": transaction.created_at
        }

    def get_materials(self, **kwargs) -> List[Dict[str, Any]]:
        """Get materials with filtering.

        Args:
            **kwargs: Filter parameters

        Returns:
            List[Dict[str, Any]]: List of materials
        """
        try:
            # Build query
            query = select(Material)

            # Apply material type filter
            if "material_type" in kwargs:
                material_type = kwargs.get("material_type")
                query = query.where(Material.material_type == material_type)

            # Apply search filter
            if "search" in kwargs:
                search_term = kwargs.get("search")
                search_pattern = f"%{search_term}%"
                query = query.where(
                    or_(
                        Material.name.ilike(search_pattern),
                        Material.description.ilike(search_pattern) if hasattr(Material, "description") else False
                    )
                )

            # Apply status filter
            if "status" in kwargs:
                query = query.where(Material.status == kwargs.get("status"))

            # Apply in-stock filter
            if kwargs.get("in_stock_only", False):
                query = query.where(Material.quantity > 0)

            # Apply leather type filter
            if "leather_type" in kwargs and kwargs["leather_type"] is not None:
                query = query.where(Material.leather_type == kwargs["leather_type"])

            # Apply quality grade filter
            if "quality_grade" in kwargs and kwargs["quality_grade"] is not None:
                query = query.where(Material.quality_grade == kwargs["quality_grade"])

            # Apply price range filters
            if "min_price" in kwargs and kwargs["min_price"] is not None:
                query = query.where(Material.price >= kwargs["min_price"])
            if "max_price" in kwargs and kwargs["max_price"] is not None:
                query = query.where(Material.price <= kwargs["max_price"])

            # Apply area range filters
            if "min_area" in kwargs and kwargs["min_area"] is not None:
                query = query.where(Material.area >= kwargs["min_area"])
            if "max_area" in kwargs and kwargs["max_area"] is not None:
                query = query.where(Material.area <= kwargs["max_area"])

            # Execute query
            result = self._session.execute(query)
            materials = result.scalars().all()

            # Convert to dictionaries
            return [self._material_to_dict(material) for material in materials]

        except SQLAlchemyError as e:
            self._logger.error(f"Database error when retrieving materials: {str(e)}")
            raise ServiceError("Failed to retrieve materials", {"error": str(e)})
        except Exception as e:
            self._logger.error(f"Unexpected error in get_materials: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def get_material(self, material_id: str) -> Dict[str, Any]:
        """Get a material by ID.

        Args:
            material_id (str): Material ID

        Returns:
            Dict[str, Any]: Material data

        Raises:
            NotFoundError: If material not found
        """
        try:
            material = self._repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            return self._material_to_dict(material)

        except NotFoundError as e:
            raise e
        except SQLAlchemyError as e:
            self._logger.error(f"Database error when retrieving material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve material {material_id}", {"error": str(e)})
        except Exception as e:
            self._logger.error(f"Unexpected error in get_material: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def create_material(self, material_data: Dict[str, Any]) -> str:
        """Create a new material.

        Args:
            material_data (Dict[str, Any]): Material data

        Returns:
            str: ID of the created material

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate and sanitize material data
            validated_data = self._validate_material_data(material_data)

            # Create material using the new model's create method
            material = Material.create(**validated_data)

            # Add to session and commit
            self._session.add(material)
            self._session.commit()

            return str(material.id)

        except ValidationError as e:
            raise e
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Database error when creating material: {str(e)}")
            raise ServiceError("Failed to create material", {"error": str(e)})
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Unexpected error in create_material: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def update_material(self, material_id: str, material_data: Dict[str, Any]) -> bool:
        """Update an existing material.

        Args:
            material_id (str): Material ID
            material_data (Dict[str, Any]): Material data

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If material not found
            ValidationError: If validation fails
        """
        try:
            # Get existing material
            material = self._repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Validate and sanitize material data
            validated_data = self._validate_material_data(material_data, is_update=True)

            # Update material using the model's update method
            material.update(**validated_data)

            # Commit changes
            self._session.commit()

            return True

        except NotFoundError as e:
            raise e
        except ValidationError as e:
            raise e
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Database error when updating material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to update material {material_id}", {"error": str(e)})
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Unexpected error in update_material: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def delete_material(self, material_id: str) -> bool:
        """Delete a material.

        Args:
            material_id (str): Material ID

        Returns:
            bool: True if successful

        Raises:
            NotFoundError: If material not found
        """
        try:
            # Get existing material
            material = self._repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Soft delete the material
            material.soft_delete()

            # Commit changes
            self._session.commit()

            return True

        except NotFoundError as e:
            raise e
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Database error when deleting material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to delete material {material_id}", {"error": str(e)})
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Unexpected error in delete_material: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def add_material_transaction(self, material_id: str, transaction_data: Dict[str, Any]) -> str:
        """Add a transaction for a material.

        Args:
            material_id (str): Material ID
            transaction_data (Dict[str, Any]): Transaction data

        Returns:
            str: Transaction ID

        Raises:
            NotFoundError: If material not found
            ValidationError: If validation fails
        """
        try:
            # Get existing material
            material = self._repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Validate transaction data
            if "transaction_type" not in transaction_data:
                raise ValidationError("Missing transaction type")
            if "quantity" not in transaction_data:
                raise ValidationError("Missing quantity")

            # Validate transaction type
            try:
                transaction_type = TransactionType(transaction_data["transaction_type"])
            except ValueError:
                raise ValidationError(f"Invalid transaction type: {transaction_data['transaction_type']}")

            # Validate quantity
            try:
                quantity = float(transaction_data["quantity"])
                if quantity <= 0:
                    raise ValidationError("Quantity must be a positive number")
            except ValueError:
                raise ValidationError("Quantity must be a valid number")

            # Create transaction
            transaction_data['material_id'] = material_id

            # Use MaterialTransaction's create method
            transaction = MaterialTransaction.create(**transaction_data)

            # Add to session and commit
            self._session.add(transaction)

            # Adjust material quantity based on transaction type
            if transaction_type in [TransactionType.PURCHASE, TransactionType.ADJUSTMENT]:
                material.quantity += quantity
            elif transaction_type in [TransactionType.USAGE, TransactionType.WASTE]:
                if material.quantity < quantity:
                    raise ValidationError("Insufficient quantity available")
                material.quantity -= quantity

            # Commit changes
            self._session.commit()

            return str(transaction.id)

        except (NotFoundError, ValidationError) as e:
            self._session.rollback()
            raise e
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Database error when adding transaction for material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to add transaction for material {material_id}", {"error": str(e)})
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Unexpected error in add_material_transaction: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def get_material_transactions(self, material_id: str) -> List[Dict[str, Any]]:
        """Get transactions for a material.

        Args:
            material_id (str): Material ID

        Returns:
            List[Dict[str, Any]]: List of transactions

        Raises:
            NotFoundError: If material not found
        """
        try:
            # Verify material exists
            material = self._repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Query transactions for the material
            query = select(MaterialTransaction).where(MaterialTransaction.material_id == material_id)
            result = self._session.execute(query)
            transactions = result.scalars().all()

            # Convert to dictionaries
            return [self._transaction_to_dict(transaction) for transaction in transactions]

        except NotFoundError as e:
            raise e
        except SQLAlchemyError as e:
            self._logger.error(f"Database error when retrieving transactions for material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve transactions for material {material_id}", {"error": str(e)})
        except Exception as e:
            self._logger.error(f"Unexpected error in get_material_transactions: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def restore_material(self, material_id: str) -> bool:
        """Restore a soft-deleted material.

        Args:
            material_id (str): Material ID

        Returns:
            bool: True if successfully restored

        Raises:
            NotFoundError: If material not found
        """
        try:
            # Get existing material
            material = self._repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Restore the material
            material.restore()

            # Commit changes
            self._session.commit()

            return True

        except NotFoundError as e:
            raise e
        except SQLAlchemyError as e:
            self._session.rollback()
            self._logger.error(f"Database error when restoring material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to restore material {material_id}", {"error": str(e)})
        except Exception as e:
            self._session.rollback()
            self._logger.error(f"Unexpected error in restore_material: {str(e)}")
            raise ServiceError("An unexpected error occurred", {"error": str(e)})

    def __repr__(self) -> str:
        """String representation of the MaterialServiceAdapter.

        Returns:
            str: A descriptive string representing the service
        """
        return f"<MaterialServiceAdapter(repository={self._repository})>"