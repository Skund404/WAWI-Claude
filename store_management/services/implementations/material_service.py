# services/implementations/material_service.py
"""
Material service implementation for managing materials and transactions.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.material_service import IMaterialService, MaterialType
from utils.circular_import_resolver import lazy_import, resolve_lazy_import
from utils.error_handler import ApplicationError

# Lazy import to avoid circular dependencies
Material = lazy_import('database.models.material', 'Material')
MaterialTransaction = lazy_import('database.models.material', 'MaterialTransaction')
MaterialQualityGrade = lazy_import('database.models.enums', 'MaterialQualityGrade')


class MaterialService(BaseService, IMaterialService):
    """Implementation of material service for managing materials and transactions."""

    def __init__(self):
        """Initialize the Material Service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._materials = []  # In-memory storage for materials (will be replaced with DB)
        self._transactions = []  # In-memory storage for transactions

    def get_material_types(self) -> List[str]:
        """Get available material types.

        Returns:
            List[str]: List of material type names
        """
        self.logger.info("Getting material types")
        return [t.name for t in MaterialType]

    def create(self, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new material.

        Args:
            material_data: Dictionary containing material properties

        Returns:
            Dict[str, Any]: Created material data

        Raises:
            ValidationError: If material data is invalid
        """
        self.logger.info("Creating new material")

        # Validate required fields
        required_fields = ['name', 'type', 'quantity']
        for field in required_fields:
            if field not in material_data:
                raise ValidationError(f"Missing required field: {field}")

        try:
            # Convert type string to enum value if needed
            if isinstance(material_data.get('type'), str):
                material_data['type'] = MaterialType[material_data['type']]

            # Convert quality grade string to enum value if present
            if 'quality_grade' in material_data and isinstance(material_data['quality_grade'], str):
                material_QualityGrade = resolve_lazy_import(MaterialQualityGrade)
                material_data['quality_grade'] = material_QualityGrade[material_data['quality_grade']]

            # Create a new material
            material_model = resolve_lazy_import(Material)
            material = material_model(**material_data)

            # Add ID if not in database mode
            if not hasattr(material, 'id') or material.id is None:
                material.id = len(self._materials) + 1
                material.created_at = datetime.now()
                material.updated_at = datetime.now()
                self._materials.append(material)

            return self._convert_material_to_dict(material)
        except KeyError as e:
            self.logger.error(f"Invalid material data: {str(e)}")
            raise ValidationError(f"Invalid material data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error creating material: {str(e)}")
            raise ApplicationError(f"Failed to create material: {str(e)}")

    def update(self, material_id: int, material_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing material.

        Args:
            material_id: ID of the material to update
            material_data: Dictionary with updated material data

        Returns:
            Dict[str, Any]: Updated material data

        Raises:
            NotFoundError: If material with given ID doesn't exist
            ValidationError: If material data is invalid
        """
        self.logger.info(f"Updating material with ID {material_id}")

        # Find material
        material = self.get_by_id(material_id, as_dict=False)

        if not material:
            raise NotFoundError(f"Material with ID {material_id} not found")

        try:
            # Convert type string to enum value if needed
            if 'type' in material_data and isinstance(material_data['type'], str):
                material_data['type'] = MaterialType[material_data['type']]

            # Convert quality grade string to enum value if present
            if 'quality_grade' in material_data and isinstance(material_data['quality_grade'], str):
                material_QualityGrade = resolve_lazy_import(MaterialQualityGrade)
                material_data['quality_grade'] = material_QualityGrade[material_data['quality_grade']]

            # Update material attributes
            for key, value in material_data.items():
                if hasattr(material, key):
                    setattr(material, key, value)

            material.updated_at = datetime.now()

            return self._convert_material_to_dict(material)
        except KeyError as e:
            self.logger.error(f"Invalid material data: {str(e)}")
            raise ValidationError(f"Invalid material data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error updating material: {str(e)}")
            raise ApplicationError(f"Failed to update material: {str(e)}")

    def delete(self, material_id: int) -> bool:
        """Delete a material.

        Args:
            material_id: ID of the material to delete

        Returns:
            bool: True if deleted successfully

        Raises:
            NotFoundError: If material with given ID doesn't exist
        """
        self.logger.info(f"Deleting material with ID {material_id}")

        # Find material index
        material = None
        material_index = -1

        for i, m in enumerate(self._materials):
            if m.id == material_id:
                material = m
                material_index = i
                break

        if material is None:
            raise NotFoundError(f"Material with ID {material_id} not found")

        # Remove material
        self._materials.pop(material_index)

        return True

    def get_by_id(self, material_id: int, as_dict: bool = True) -> Union[Dict[str, Any], Any]:
        """Get a material by ID.

        Args:
            material_id: ID of the material to retrieve
            as_dict: Whether to return as dictionary (True) or model instance (False)

        Returns:
            Union[Dict[str, Any], Any]: Material data or model instance

        Raises:
            NotFoundError: If material with given ID doesn't exist
        """
        self.logger.info(f"Getting material with ID {material_id}")

        material = None

        for m in self._materials:
            if m.id == material_id:
                material = m
                break

        if material is None:
            raise NotFoundError(f"Material with ID {material_id} not found")

        if as_dict:
            return self._convert_material_to_dict(material)
        else:
            return material

    def get_materials(self, material_type: Optional[Union[MaterialType, str]] = None) -> List[Dict[str, Any]]:
        """Get materials, optionally filtered by type.

        Args:
            material_type: Optional material type to filter by

        Returns:
            List[Dict[str, Any]]: List of materials
        """
        self.logger.info("Getting materials")

        # Convert string type to enum if needed
        if isinstance(material_type, str):
            try:
                material_type = MaterialType[material_type]
            except KeyError:
                self.logger.warning(f"Invalid material type: {material_type}")
                material_type = None

        # Filter materials by type if specified
        if material_type is not None:
            materials = [m for m in self._materials if m.type == material_type]
        else:
            materials = self._materials

        return [self._convert_material_to_dict(m) for m in materials]

    def record_material_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record a material transaction (purchase, usage, etc.).

        Args:
            transaction_data: Dictionary with transaction details

        Returns:
            Dict[str, Any]: Transaction data

        Raises:
            ValidationError: If transaction data is invalid
            NotFoundError: If referenced material doesn't exist
        """
        self.logger.info("Recording material transaction")

        # Validate required fields
        required_fields = ['material_id', 'quantity', 'transaction_type']
        for field in required_fields:
            if field not in transaction_data:
                raise ValidationError(f"Missing required field: {field}")

        # Check if material exists
        material_id = transaction_data['material_id']
        material = None

        for m in self._materials:
            if m.id == material_id:
                material = m
                break

        if material is None:
            raise NotFoundError(f"Material with ID {material_id} not found")

        try:
            # Create transaction
            transaction_model = resolve_lazy_import(MaterialTransaction)
            transaction = transaction_model(
                material_id=material_id,
                quantity=transaction_data['quantity'],
                transaction_type=transaction_data['transaction_type'],
                description=transaction_data.get('description', ''),
                date=transaction_data.get('date', datetime.now()),
                user_id=transaction_data.get('user_id'),
                project_id=transaction_data.get('project_id')
            )

            # Add ID if not in database mode
            if not hasattr(transaction, 'id') or transaction.id is None:
                transaction.id = len(self._transactions) + 1
                transaction.created_at = datetime.now()
                self._transactions.append(transaction)

            # Update material quantity based on transaction type
            if transaction.transaction_type in ['purchase', 'return', 'adjustment_add']:
                material.quantity += transaction.quantity
            elif transaction.transaction_type in ['usage', 'waste', 'adjustment_subtract']:
                material.quantity -= transaction.quantity
                if material.quantity < 0:
                    material.quantity = 0

            material.updated_at = datetime.now()

            return self._convert_transaction_to_dict(transaction)
        except Exception as e:
            self.logger.error(f"Error recording transaction: {str(e)}")
            raise ApplicationError(f"Failed to record transaction: {str(e)}")

    def get_material_transactions(self, material_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get material transactions, optionally filtered by material ID.

        Args:
            material_id: Optional material ID to filter by

        Returns:
            List[Dict[str, Any]]: List of transactions
        """
        self.logger.info("Getting material transactions")

        # Filter transactions by material ID if specified
        if material_id is not None:
            transactions = [t for t in self._transactions if t.material_id == material_id]
        else:
            transactions = self._transactions

        return [self._convert_transaction_to_dict(t) for t in transactions]

    def calculate_material_cost(self, material_id: int, quantity: float) -> Dict[str, float]:
        """Calculate cost for a given quantity of material.

        Args:
            material_id: ID of the material
            quantity: Quantity to calculate cost for

        Returns:
            Dict[str, float]: Dictionary with cost details

        Raises:
            NotFoundError: If material with given ID doesn't exist
            ValidationError: If quantity is invalid
        """
        self.logger.info(f"Calculating cost for material ID {material_id}, quantity {quantity}")

        if quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")

        # Get material
        material = self.get_by_id(material_id, as_dict=False)

        # Calculate costs
        unit_price = material.unit_price or 0.0
        base_cost = unit_price * quantity

        # Apply waste factor if available
        waste_factor = material.waste_factor or 0.1  # Default 10% waste
        waste_cost = base_cost * waste_factor

        # Calculate total cost
        total_cost = base_cost + waste_cost

        return {
            'unit_price': unit_price,
            'base_cost': base_cost,
            'waste_factor': waste_factor,
            'waste_cost': waste_cost,
            'total_cost': total_cost
        }

    def _convert_material_to_dict(self, material: Any) -> Dict[str, Any]:
        """Convert Material model to dictionary.

        Args:
            material: Material model instance

        Returns:
            Dict[str, Any]: Dictionary representation of material
        """

        # Safe access to enum values
        def safe_enum_value(enum_obj):
            if enum_obj is None:
                return None
            return enum_obj.name

        return {
            'id': material.id,
            'name': material.name,
            'type': safe_enum_value(material.type),
            'description': material.description,
            'quantity': material.quantity,
            'unit_price': material.unit_price,
            'unit_of_measure': material.unit_of_measure,
            'supplier_id': material.supplier_id if hasattr(material, 'supplier_id') else None,
            'quality_grade': safe_enum_value(material.quality_grade) if hasattr(material, 'quality_grade') else None,
            'waste_factor': material.waste_factor if hasattr(material, 'waste_factor') else None,
            'reorder_point': material.reorder_point if hasattr(material, 'reorder_point') else None,
            'reorder_quantity': material.reorder_quantity if hasattr(material, 'reorder_quantity') else None,
            'notes': material.notes if hasattr(material, 'notes') else None,
            'created_at': material.created_at,
            'updated_at': material.updated_at
        }

    def _convert_transaction_to_dict(self, transaction: Any) -> Dict[str, Any]:
        """Convert MaterialTransaction model to dictionary.

        Args:
            transaction: MaterialTransaction model instance

        Returns:
            Dict[str, Any]: Dictionary representation of transaction
        """
        return {
            'id': transaction.id,
            'material_id': transaction.material_id,
            'quantity': transaction.quantity,
            'transaction_type': transaction.transaction_type,
            'description': transaction.description,
            'date': transaction.date,
            'user_id': transaction.user_id if hasattr(transaction, 'user_id') else None,
            'project_id': transaction.project_id if hasattr(transaction, 'project_id') else None,
            'created_at': transaction.created_at if hasattr(transaction, 'created_at') else None
        }