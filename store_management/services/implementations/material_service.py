# services/implementations/material_service.py
import logging
from sqlalchemy import or_, select

from database.models.enums import InventoryStatus, MaterialType, TransactionType
from database.models.material import Material
from database.models.base import ModelValidationError
from database.repositories.material_repository import MaterialRepository
from database.sqlalchemy.session import get_db_session

from services.base_service import BaseService, NotFoundError, ValidationError, ServiceError
from services.interfaces.material_service import IMaterialService, MaterialType as IMaterialType

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
        self._session = session
        self._repository = MaterialRepository(session)
        self._logger = logging.getLogger(__name__)

    # IMaterialService interface implementation methods

    def create(self, data: Dict[str, Any]) -> Any:
        """Create a new material.

        Args:
            data: Material creation data

        Returns:
            Created material ID
        """
        return self.create_material(data)

    def get_by_id(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get material by ID.

        Args:
            material_id: ID of the material

        Returns:
            Material data or None if not found
        """
        try:
            return self.get_material_by_id(int(material_id))
        except ValueError:
            raise ValidationError(f"Invalid material ID: {material_id}")

    def update(self, material_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing material.

        Args:
            material_id: ID of the material
            updates: Update data

        Returns:
            Updated material data or None if not found
        """
        try:
            return self.update_material(int(material_id), updates)
        except ValueError:
            raise ValidationError(f"Invalid material ID: {material_id}")

    def delete(self, material_id: str) -> bool:
        """Delete a material.

        Args:
            material_id: ID of the material

        Returns:
            True if successful, False otherwise
        """
        try:
            return self.delete_material(int(material_id))
        except ValueError:
            raise ValidationError(f"Invalid material ID: {material_id}")

    def record_material_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a material transaction.

        Args:
            transaction_data: Transaction data including material_id, transaction_type,
                            quantity, and optional notes

        Returns:
            Created transaction record
        """
        try:
            # Validate required fields
            self.validate_input(transaction_data, ['material_id', 'transaction_type', 'quantity'])

            material_id = transaction_data.get('material_id')
            try:
                material_id = int(material_id)
            except ValueError:
                raise ValidationError(f"Invalid material ID: {material_id}")

            # Get the material
            material = self.repository.get_by_id(material_id)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Get transaction details
            transaction_type = transaction_data.get('transaction_type')
            quantity = float(transaction_data.get('quantity', 0))
            notes = transaction_data.get('notes', '')

            # Create transaction record
            transaction = self.repository.create_transaction(
                material_id=material_id,
                transaction_type=transaction_type,
                quantity=quantity,
                notes=notes
            )

            # Update material quantity based on transaction type
            if transaction_type in [TransactionType.PURCHASE, TransactionType.ADJUSTMENT]:
                material.quantity += quantity
            elif transaction_type in [TransactionType.USAGE, TransactionType.WASTE]:
                if material.quantity < quantity:
                    raise ValidationError(
                        f"Insufficient quantity available. Current: {material.quantity}, Requested: {quantity}")
                material.quantity -= quantity

            # Save changes
            self._session.commit()

            log_info(f"Recorded transaction for material {material_id}: {transaction_type.name}, {quantity}")

            # Return transaction data
            return {
                'id': transaction.id,
                'material_id': material_id,
                'transaction_type': transaction_type,
                'quantity': quantity,
                'date': transaction.date,
                'notes': notes
            }

        except ValueError as e:
            raise ValidationError(str(e))
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._session.rollback()
            log_error(f"Error recording material transaction: {str(e)}")
            raise ServiceError(f"Failed to record material transaction: {str(e)}")

    def get_material_transactions(self, material_id: Optional[str] = None,
                                  transaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get material transactions with optional filtering.

        Args:
            material_id: Optional material ID to filter by
            transaction_type: Optional transaction type to filter by

        Returns:
            List of transactions
        """
        try:
            # Convert material_id to int if provided
            material_id_int = None
            if material_id:
                try:
                    material_id_int = int(material_id)
                except ValueError:
                    raise ValidationError(f"Invalid material ID: {material_id}")

            # Convert transaction_type string to enum if provided
            transaction_type_enum = None
            if transaction_type:
                try:
                    transaction_type_enum = TransactionType[transaction_type]
                except KeyError:
                    raise ValidationError(f"Invalid transaction type: {transaction_type}")

            # Get transactions with filters
            transactions = self.repository.get_transactions(
                material_id=material_id_int,
                transaction_type=transaction_type_enum
            )

            # Convert to dictionary format
            return [
                {
                    'id': t.id,
                    'material_id': t.material_id,
                    'transaction_type': t.transaction_type,
                    'quantity': t.quantity,
                    'date': t.date,
                    'notes': t.notes
                }
                for t in transactions
            ]

        except ValidationError:
            raise
        except Exception as e:
            log_error(f"Error retrieving material transactions: {str(e)}")
            raise ServiceError(f"Failed to retrieve material transactions: {str(e)}")

    def calculate_material_cost(self, material_id: str, quantity: float) -> float:
        """Calculate cost for a given material quantity.

        Args:
            material_id: ID of the material
            quantity: Quantity of material

        Returns:
            Calculated cost
        """
        try:
            # Convert material_id to int
            try:
                material_id_int = int(material_id)
            except ValueError:
                raise ValidationError(f"Invalid material ID: {material_id}")

            # Get material
            material = self.repository.get_by_id(material_id_int)
            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Calculate cost
            price = getattr(material, 'price', 0.0)
            if price is None:
                price = 0.0

            return price * quantity

        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            log_error(f"Error calculating material cost: {str(e)}")
            raise ServiceError(f"Failed to calculate material cost: {str(e)}")

    def get_material_types(self) -> List[str]:
        """Get all available material types.

        Returns:
            List of material type names
        """
        try:
            # Return a list of material type names
            return [material_type.name for material_type in MaterialType]
        except Exception as e:
            log_error(f"Error retrieving material types: {str(e)}")
            raise ServiceError(f"Failed to retrieve material types: {str(e)}")

    # Updated get_materials method with proper enum handling
    def get_materials(self, material_type=None, **kwargs):
        """
        Get materials with the given material type and optional filters.

        Args:
            material_type: The type of material to filter by.
            **kwargs: Additional filters to apply.

        Returns:
            List of materials matching the filters.
        """
        try:
            self._logger.info(f"get_materials called with material_type={material_type}")

            # Build filter conditions based on keyword arguments
            conditions = []

            # Handle material_type parameter (either as positional or keyword arg)
            if material_type is not None:
                # Handle different ways material_type might be provided
                if hasattr(material_type, 'name'):
                    # It's an enum object, use its name
                    material_type_value = material_type.name
                    self._logger.info(f"Using material_type enum name: {material_type_value}")
                else:
                    # It's something else (string, etc.), use it directly
                    material_type_value = material_type
                    self._logger.info(f"Using material_type value directly: {material_type_value}")

                conditions.append(Material.material_type == material_type_value)

            # Add search filter if provided
            if "search" in kwargs:
                search_term = kwargs["search"]
                conditions.append(
                    or_(
                        Material.name.ilike(f"%{search_term}%"),
                        Material.description.ilike(f"%{search_term}%"),
                    )
                )

            # Add optional status filter
            if "status" in kwargs:
                status = kwargs["status"]
                if hasattr(status, 'name'):  # Enum object
                    conditions.append(Material.status == status.name)
                else:  # String value or other
                    conditions.append(Material.status == status)

            # Add other filters
            if "in_stock_only" in kwargs and kwargs["in_stock_only"]:
                conditions.append(Material.quantity > 0)

            if "min_price" in kwargs:
                conditions.append(Material.price >= kwargs["min_price"])

            if "max_price" in kwargs:
                conditions.append(Material.price <= kwargs["max_price"])

            if "min_area" in kwargs:
                conditions.append(Material.area >= kwargs["min_area"])

            if "max_area" in kwargs:
                conditions.append(Material.area <= kwargs["max_area"])

            # Leather specific filters
            if "leather_type" in kwargs:
                leather_type = kwargs["leather_type"]
                if hasattr(leather_type, 'name'):  # Enum object
                    conditions.append(Material.leather_type == leather_type.name)
                else:  # String value or other
                    conditions.append(Material.leather_type == leather_type)

            if "quality_grade" in kwargs:
                quality_grade = kwargs["quality_grade"]
                if hasattr(quality_grade, 'name'):  # Enum object
                    conditions.append(Material.quality_grade == quality_grade.name)
                else:  # String value or other
                    conditions.append(Material.quality_grade == quality_grade)

            # Create the base query
            query = select(Material)

            # Apply filters if any
            if conditions:
                query = query.where(*conditions)

            # Execute the query
            materials = self._session.execute(query).scalars().all()
            self._logger.info(f"Found {len(materials)} materials")

            # Convert materials to dictionaries with serialized enum values
            result = []
            for material in materials:
                material_dict = self.to_dict(material)

                # Serialize enum values
                for key, value in material_dict.items():
                    material_dict[key] = self._serialize_enum_value(value)

                result.append(material_dict)

            return result

        except SQLAlchemyError as e:
            # Log detailed SQLAlchemy error
            self._logger.error(f"Database error in get_materials: {e}")
            raise
        except Exception as e:
            # Log unexpected errors
            self._logger.error(f"Unexpected error in get_materials: {e}")
            raise ServiceError(f"Failed to retrieve materials: {str(e)}") from e

    def _serialize_enum_value(self, value):
        """
        Safely serialize enum values or return the original value.

        Args:
            value: The value to serialize

        Returns:
            Serialized value (enum name or original value)
        """
        try:
            # If it's an enum, return its name
            if hasattr(value, 'name'):
                return value.name
            # If it's an enum-like object with a string representation
            elif hasattr(value, '__str__'):
                return str(value)
            # Return the original value if no special handling is needed
            return value
        except Exception as e:
            self._logger.warning(f"Error serializing enum value: {e}")
            return str(value)

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

            self._session.commit()
            log_info(f"Adjusted material {material_id} quantity by {quantity_change}")

            return self.to_dict(material)
        except NotFoundError:
            # Re-raise not found error
            raise
        except ValueError as e:
            # Convert ValueError to ValidationError
            raise ValidationError(str(e))
        except Exception as e:
            self._session.rollback()
            log_error(f"Error adjusting material quantity: {str(e)}")
            raise ServiceError(f"Failed to adjust material quantity: {str(e)}")

    # Helper methods

    def validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that all required fields are present in the data.

        Args:
            data: Data dictionary to validate
            required_fields: List of field names that are required

        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

    def to_dict(self, material) -> Dict[str, Any]:
        """Convert material model to dictionary.

        Args:
            material: Material model instance

        Returns:
            Dictionary representation of the material
        """
        if hasattr(material, "to_dict"):
            return material.to_dict()

        # Default implementation if to_dict not available
        material_dict = {
            "id": getattr(material, "id", None),
            "name": getattr(material, "name", ""),
            "description": getattr(material, "description", ""),
            "material_type": getattr(material, "material_type", None),
            "price": getattr(material, "price", 0.0),
            "quantity": getattr(material, "quantity", 0),
            "status": getattr(material, "status", None),
        }

        # Add leather-specific attributes if present
        for attr in ["leather_type", "quality_grade", "area", "thickness", "color", "supplier_name"]:
            if hasattr(material, attr):
                material_dict[attr] = getattr(material, attr)

        return material_dict