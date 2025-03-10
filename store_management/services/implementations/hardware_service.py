# services/implementations/hardware_service.py
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.material import Hardware
from database.models.enums import HardwareType, HardwareMaterial, HardwareFinish, InventoryStatus
from database.repositories.hardware_repository import HardwareRepository
from database.repositories.component_repository import ComponentRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.supplier_repository import SupplierRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.implementations.material_service import MaterialService
from services.interfaces.hardware_service import IHardwareService

from di.core import inject


class HardwareService(MaterialService, IHardwareService):
    """Implementation of the Hardware Service interface.

    This service provides specialized functionality for managing hardware materials
    used in leatherworking projects, such as buckles, rivets, snaps, etc.
    """

    @inject
    def __init__(self,
                 session: Session,
                 hardware_repository: Optional[HardwareRepository] = None,
                 component_repository: Optional[ComponentRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None):
        """Initialize the Hardware Service.

        Args:
            session: SQLAlchemy database session
            hardware_repository: Optional HardwareRepository instance
            component_repository: Optional ComponentRepository instance
            inventory_repository: Optional InventoryRepository instance
            supplier_repository: Optional SupplierRepository instance
        """
        super().__init__(session)
        self.hardware_repository = hardware_repository or HardwareRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, hardware_id: int) -> Dict[str, Any]:
        """Retrieve a hardware item by its ID.

        Args:
            hardware_id: The ID of the hardware to retrieve

        Returns:
            A dictionary representation of the hardware

        Raises:
            NotFoundError: If the hardware does not exist
        """
        try:
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")
            return self._to_dict(hardware)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve hardware: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all hardware items with optional filtering.

        Args:
            filters: Optional filters to apply to the hardware query

        Returns:
            List of dictionaries representing hardware items
        """
        try:
            hardware_items = self.hardware_repository.get_all(filters)
            return [self._to_dict(hardware) for hardware in hardware_items]
        except Exception as e:
            self.logger.error(f"Error retrieving hardware items: {str(e)}")
            raise ServiceError(f"Failed to retrieve hardware items: {str(e)}")

    def create(self, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new hardware item.

        Args:
            hardware_data: Dictionary containing hardware data

        Returns:
            Dictionary representation of the created hardware

        Raises:
            ValidationError: If the hardware data is invalid
        """
        try:
            # Validate the hardware data
            self._validate_hardware_data(hardware_data)

            # Set material_type to HARDWARE
            hardware_data['material_type'] = 'HARDWARE'

            # Check supplier if supplier_id is provided
            if 'supplier_id' in hardware_data and hardware_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(hardware_data['supplier_id'])
                if not supplier:
                    raise NotFoundError(f"Supplier with ID {hardware_data['supplier_id']} not found")

            # Create the hardware within a transaction
            with self.transaction():
                hardware = Hardware(**hardware_data)
                created_hardware = self.hardware_repository.create(hardware)

                # Create inventory entry for the hardware if initial_quantity is provided
                if 'initial_quantity' in hardware_data:
                    initial_quantity = hardware_data.get('initial_quantity', 0)
                    inventory_data = {
                        'item_type': 'material',
                        'item_id': created_hardware.id,
                        'quantity': initial_quantity,
                        'status': InventoryStatus.IN_STOCK.value if initial_quantity > 0 else InventoryStatus.OUT_OF_STOCK.value,
                        'storage_location': hardware_data.get('storage_location', '')
                    }
                    self.inventory_repository.create(inventory_data)

                return self._to_dict(created_hardware)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating hardware: {str(e)}")
            raise ServiceError(f"Failed to create hardware: {str(e)}")

    def update(self, hardware_id: int, hardware_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing hardware item.

        Args:
            hardware_id: ID of the hardware to update
            hardware_data: Dictionary containing updated hardware data

        Returns:
            Dictionary representation of the updated hardware

        Raises:
            NotFoundError: If the hardware does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Validate hardware data
            self._validate_hardware_data(hardware_data, update=True)

            # Check supplier if supplier_id is provided
            if 'supplier_id' in hardware_data and hardware_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(hardware_data['supplier_id'])
                if not supplier:
                    raise NotFoundError(f"Supplier with ID {hardware_data['supplier_id']} not found")

            # Update the hardware within a transaction
            with self.transaction():
                updated_hardware = self.hardware_repository.update(hardware_id, hardware_data)
                return self._to_dict(updated_hardware)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to update hardware: {str(e)}")

    def delete(self, hardware_id: int) -> bool:
        """Delete a hardware item by its ID.

        Args:
            hardware_id: ID of the hardware to delete

        Returns:
            True if the hardware was successfully deleted

        Raises:
            NotFoundError: If the hardware does not exist
            ServiceError: If the hardware cannot be deleted (e.g., in use)
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Check if hardware is used in any components
            components_using = self.get_components_using(hardware_id)
            if components_using:
                raise ServiceError(
                    f"Cannot delete hardware {hardware_id} as it is used in {len(components_using)} components")

            # Delete the hardware within a transaction
            with self.transaction():
                # Delete inventory entries first
                inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=hardware_id)
                for entry in inventory_entries:
                    self.inventory_repository.delete(entry.id)

                # Then delete the hardware
                self.hardware_repository.delete(hardware_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to delete hardware: {str(e)}")

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find hardware items by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching hardware items
        """
        try:
            hardware_items = self.hardware_repository.find_by_name(name)
            return [self._to_dict(hardware) for hardware in hardware_items]
        except Exception as e:
            self.logger.error(f"Error finding hardware by name '{name}': {str(e)}")
            raise ServiceError(f"Failed to find hardware by name: {str(e)}")

    def find_by_type(self, hardware_type: str) -> List[Dict[str, Any]]:
        """Find hardware items by type.

        Args:
            hardware_type: Hardware type to filter by

        Returns:
            List of dictionaries representing hardware of the specified type
        """
        try:
            # Validate hardware type
            self._validate_hardware_type(hardware_type)

            hardware_items = self.hardware_repository.find_by_type(hardware_type)
            return [self._to_dict(hardware) for hardware in hardware_items]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding hardware by type '{hardware_type}': {str(e)}")
            raise ServiceError(f"Failed to find hardware by type: {str(e)}")

    def find_by_material(self, material: str) -> List[Dict[str, Any]]:
        """Find hardware items by material.

        Args:
            material: Material type to filter by

        Returns:
            List of dictionaries representing hardware made of the specified material
        """
        try:
            # Validate hardware material
            self._validate_hardware_material(material)

            hardware_items = self.hardware_repository.find_by_material(material)
            return [self._to_dict(hardware) for hardware in hardware_items]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding hardware by material '{material}': {str(e)}")
            raise ServiceError(f"Failed to find hardware by material: {str(e)}")

    def find_by_finish(self, finish: str) -> List[Dict[str, Any]]:
        """Find hardware items by finish.

        Args:
            finish: Finish type to filter by

        Returns:
            List of dictionaries representing hardware with the specified finish
        """
        try:
            # Validate hardware finish
            self._validate_hardware_finish(finish)

            hardware_items = self.hardware_repository.find_by_finish(finish)
            return [self._to_dict(hardware) for hardware in hardware_items]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding hardware by finish '{finish}': {str(e)}")
            raise ServiceError(f"Failed to find hardware by finish: {str(e)}")

    def get_by_size(self, size: str) -> List[Dict[str, Any]]:
        """Find hardware items by size.

        Args:
            size: Size to filter by

        Returns:
            List of dictionaries representing hardware of the specified size
        """
        try:
            hardware_items = self.hardware_repository.find_by_size(size)
            return [self._to_dict(hardware) for hardware in hardware_items]
        except Exception as e:
            self.logger.error(f"Error finding hardware by size '{size}': {str(e)}")
            raise ServiceError(f"Failed to find hardware by size: {str(e)}")

    def get_inventory_status(self, hardware_id: int) -> Dict[str, Any]:
        """Get the current inventory status of a hardware item.

        Args:
            hardware_id: ID of the hardware

        Returns:
            Dictionary containing inventory information

        Raises:
            NotFoundError: If the hardware does not exist
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Get inventory entry
            inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=hardware_id)

            if not inventory_entries:
                return {
                    'hardware_id': hardware_id,
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': '',
                    'last_updated': None
                }
            else:
                # Use the first inventory entry (should be only one per hardware)
                inventory = inventory_entries[0]
                return {
                    'hardware_id': hardware_id,
                    'inventory_id': inventory.id,
                    'quantity': inventory.quantity,
                    'status': inventory.status.name if hasattr(inventory.status, 'name') else str(inventory.status),
                    'storage_location': getattr(inventory, 'storage_location', ''),
                    'last_updated': inventory.updated_at.isoformat() if hasattr(inventory,
                                                                                'updated_at') and inventory.updated_at else None
                }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting inventory status for hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to get inventory status: {str(e)}")

    def adjust_inventory(self, hardware_id: int,
                         quantity: int,
                         reason: str) -> Dict[str, Any]:
        """Adjust the inventory of a hardware item.

        Args:
            hardware_id: ID of the hardware
            quantity: Quantity to adjust (positive or negative)
            reason: Reason for the adjustment

        Returns:
            Dictionary containing updated inventory information

        Raises:
            NotFoundError: If the hardware does not exist
            ValidationError: If the adjustment would result in negative inventory
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Get inventory entry
            inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=hardware_id)

            if not inventory_entries:
                # If no inventory entry exists and quantity is positive, create one
                if quantity <= 0:
                    raise ValidationError(f"Cannot adjust inventory by {quantity} when no inventory exists")

                with self.transaction():
                    inventory_data = {
                        'item_type': 'material',
                        'item_id': hardware_id,
                        'quantity': quantity,
                        'status': InventoryStatus.IN_STOCK.value if quantity > 0 else InventoryStatus.OUT_OF_STOCK.value,
                        'storage_location': '',
                        'notes': reason
                    }
                    inventory = self.inventory_repository.create(inventory_data)

                    # Create transaction record if transaction repository is available
                    if hasattr(self, 'transaction_repository'):
                        transaction_data = {
                            'item_type': 'material',
                            'item_id': hardware_id,
                            'quantity': abs(quantity),
                            'type': 'RESTOCK',
                            'notes': reason
                        }
                        self.transaction_repository.create(transaction_data)

                    return {
                        'hardware_id': hardware_id,
                        'inventory_id': inventory.id,
                        'quantity': inventory.quantity,
                        'status': inventory.status.name if hasattr(inventory.status, 'name') else str(inventory.status),
                        'storage_location': getattr(inventory, 'storage_location', ''),
                        'last_updated': inventory.updated_at.isoformat() if hasattr(inventory,
                                                                                    'updated_at') and inventory.updated_at else None
                    }
            else:
                # Use the first inventory entry (should be only one per hardware)
                inventory = inventory_entries[0]

                # Check if adjustment would result in negative inventory
                if inventory.quantity + quantity < 0:
                    raise ValidationError(
                        f"Cannot reduce inventory below zero (current: {inventory.quantity}, adjustment: {quantity})")

                # Update inventory within a transaction
                with self.transaction():
                    # Determine inventory status based on new quantity
                    new_quantity = inventory.quantity + quantity
                    if new_quantity == 0:
                        status = InventoryStatus.OUT_OF_STOCK.value
                    elif new_quantity < 5:  # Arbitrary threshold, could be configurable
                        status = InventoryStatus.LOW_STOCK.value
                    else:
                        status = InventoryStatus.IN_STOCK.value

                    # Update inventory
                    inventory_data = {
                        'quantity': new_quantity,
                        'status': status
                    }

                    updated_inventory = self.inventory_repository.update(inventory.id, inventory_data)

                    # Create transaction record if transaction repository is available
                    if hasattr(self, 'transaction_repository'):
                        transaction_type = 'USAGE' if quantity < 0 else 'RESTOCK'
                        transaction_data = {
                            'item_type': 'material',
                            'item_id': hardware_id,
                            'quantity': abs(quantity),
                            'type': transaction_type,
                            'notes': reason
                        }
                        self.transaction_repository.create(transaction_data)

                    return {
                        'hardware_id': hardware_id,
                        'inventory_id': updated_inventory.id,
                        'quantity': updated_inventory.quantity,
                        'status': updated_inventory.status.name if hasattr(updated_inventory.status, 'name') else str(
                            updated_inventory.status),
                        'storage_location': getattr(updated_inventory, 'storage_location', ''),
                        'last_updated': updated_inventory.updated_at.isoformat() if hasattr(updated_inventory,
                                                                                            'updated_at') and updated_inventory.updated_at else None
                    }
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error adjusting inventory for hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to adjust inventory: {str(e)}")

    def get_components_using(self, hardware_id: int) -> List[Dict[str, Any]]:
        """Get components that use a specific hardware item.

        Args:
            hardware_id: ID of the hardware

        Returns:
            List of dictionaries representing components that use the hardware

        Raises:
            NotFoundError: If the hardware does not exist
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Get components using the hardware
            components_with_qty = self.component_repository.get_components_using_material(hardware_id)

            result = []
            for component, quantity in components_with_qty:
                component_dict = {
                    'id': component.id,
                    'name': component.name,
                    'component_type': component.component_type.name if hasattr(component.component_type,
                                                                               'name') else str(
                        component.component_type),
                    'quantity': quantity
                }
                result.append(component_dict)

            return result
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting components using hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to get components using hardware: {str(e)}")

    def get_usage_history(self, hardware_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the usage history for a hardware item.

        Args:
            hardware_id: ID of the hardware
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            List of dictionaries containing usage records

        Raises:
            NotFoundError: If the hardware does not exist
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Check if transaction repository is available
            if not hasattr(self, 'transaction_repository'):
                return []

            # Parse dates if provided
            start_datetime = None
            end_datetime = None

            if start_date:
                try:
                    start_datetime = datetime.fromisoformat(start_date)
                except ValueError:
                    raise ValidationError(f"Invalid start date format: {start_date}. Use ISO format (YYYY-MM-DD).")

            if end_date:
                try:
                    end_datetime = datetime.fromisoformat(end_date)
                except ValueError:
                    raise ValidationError(f"Invalid end date format: {end_date}. Use ISO format (YYYY-MM-DD).")

            # Get transactions
            transactions = self.transaction_repository.get_by_item(
                item_type='material',
                item_id=hardware_id,
                start_date=start_datetime,
                end_date=end_datetime
            )

            return [self._transaction_to_dict(transaction) for transaction in transactions]
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error getting usage history for hardware {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to get usage history: {str(e)}")

    def get_compatible_hardware(self, hardware_id: int) -> List[Dict[str, Any]]:
        """Get hardware items that are compatible with the specified hardware.

        Args:
            hardware_id: ID of the hardware

        Returns:
            List of dictionaries representing compatible hardware items

        Raises:
            NotFoundError: If the hardware does not exist
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Get compatible hardware
            compatible_hardware = self.hardware_repository.get_compatible_hardware(hardware_id)

            return [self._to_dict(h) for h in compatible_hardware]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting compatible hardware for {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to get compatible hardware: {str(e)}")

    def set_compatibility(self, hardware_id: int,
                          compatible_id: int,
                          is_compatible: bool = True) -> bool:
        """Set compatibility between two hardware items.

        Args:
            hardware_id: ID of the first hardware item
            compatible_id: ID of the second hardware item
            is_compatible: Whether the items are compatible

        Returns:
            True if the compatibility was successfully set

        Raises:
            NotFoundError: If either hardware item does not exist
        """
        try:
            # Verify hardware exists
            hardware = self.hardware_repository.get_by_id(hardware_id)
            if not hardware:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            # Verify compatible hardware exists
            compatible_hardware = self.hardware_repository.get_by_id(compatible_id)
            if not compatible_hardware:
                raise NotFoundError(f"Hardware with ID {compatible_id} not found")

            # Check if compatibility already exists in the desired state
            existing_compatibility = self.hardware_repository.check_compatibility(hardware_id, compatible_id)

            if existing_compatibility == is_compatible:
                # Already in the desired state
                return True

            # Set compatibility within a transaction
            with self.transaction():
                if is_compatible:
                    # Add compatibility
                    self.hardware_repository.add_compatibility(hardware_id, compatible_id)
                else:
                    # Remove compatibility
                    self.hardware_repository.remove_compatibility(hardware_id, compatible_id)

                return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(
                f"Error setting compatibility between hardware {hardware_id} and {compatible_id}: {str(e)}")
            raise ServiceError(f"Failed to set compatibility: {str(e)}")

    def _validate_hardware_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate hardware data.

        Args:
            data: Hardware data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for new hardware
        if not update:
            required_fields = ['name', 'hardware_type']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate hardware type if provided
        if 'hardware_type' in data:
            self._validate_hardware_type(data['hardware_type'])

        # Validate hardware material if provided
        if 'hardware_material' in data:
            self._validate_hardware_material(data['hardware_material'])

        # Validate hardware finish if provided
        if 'finish' in data:
            self._validate_hardware_finish(data['finish'])

        # Validate price/cost if provided
        if 'unit_cost' in data:
            try:
                unit_cost = float(data['unit_cost'])
                if unit_cost < 0:
                    raise ValidationError("Unit cost cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Unit cost must be a valid number")

        # Validate initial_quantity if provided
        if 'initial_quantity' in data:
            try:
                quantity = int(data['initial_quantity'])
                if quantity < 0:
                    raise ValidationError("Initial quantity cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Initial quantity must be a valid integer")

    def _validate_hardware_type(self, hardware_type: str) -> None:
        """Validate that the hardware type is a valid enum value.

        Args:
            hardware_type: Hardware type to validate

        Raises:
            ValidationError: If the hardware type is invalid
        """
        try:
            # Check if the type is a valid enum value
            HardwareType[hardware_type]
        except (KeyError, ValueError):
            valid_types = [t.name for t in HardwareType]
            raise ValidationError(f"Invalid hardware type: {hardware_type}. Valid types are: {valid_types}")

    def _validate_hardware_material(self, hardware_material: str) -> None:
        """Validate that the hardware material is a valid enum value.

        Args:
            hardware_material: Hardware material to validate

        Raises:
            ValidationError: If the hardware material is invalid
        """
        try:
            # Check if the material is a valid enum value
            HardwareMaterial[hardware_material]
        except (KeyError, ValueError):
            valid_materials = [m.name for m in HardwareMaterial]
            raise ValidationError(
                f"Invalid hardware material: {hardware_material}. Valid materials are: {valid_materials}")

    def _validate_hardware_finish(self, hardware_finish: str) -> None:
        """Validate that the hardware finish is a valid enum value.

        Args:
            hardware_finish: Hardware finish to validate

        Raises:
            ValidationError: If the hardware finish is invalid
        """
        try:
            # Check if the finish is a valid enum value
            HardwareFinish[hardware_finish]
        except (KeyError, ValueError):
            valid_finishes = [f.name for f in HardwareFinish]
            raise ValidationError(f"Invalid hardware finish: {hardware_finish}. Valid finishes are: {valid_finishes}")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, Hardware):
            result = {
                'id': obj.id,
                'name': obj.name,
                'material_type': 'HARDWARE',
                'hardware_type': obj.hardware_type.name if hasattr(obj.hardware_type, 'name') else str(
                    obj.hardware_type),
                'hardware_material': obj.hardware_material.name if hasattr(obj.hardware_material, 'name') else getattr(
                    obj, 'hardware_material', None),
                'finish': obj.finish.name if hasattr(obj, 'finish', None) and hasattr(obj.finish, 'name') else getattr(
                    obj, 'finish', None),
                'size': getattr(obj, 'size', None),
                'unit_cost': getattr(obj, 'unit_cost', None),
                'supplier_id': getattr(obj, 'supplier_id', None),
                'created_at': obj.created_at.isoformat() if hasattr(obj, 'created_at') and obj.created_at else None,
                'updated_at': obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None,
            }

            # Include other fields if present
            optional_fields = ['description', 'sku', 'minimum_order_quantity', 'reorder_threshold', 'unit']

            for field in optional_fields:
                if hasattr(obj, field):
                    result[field] = getattr(obj, field)

            return result
        elif hasattr(obj, '__dict__'):
            # Generic conversion for other model types
            result = {}
            for k, v in obj.__dict__.items():
                if not k.startswith('_'):
                    # Handle datetime objects
                    if isinstance(v, datetime):
                        result[k] = v.isoformat()
                    # Handle enum objects
                    elif hasattr(v, 'name'):
                        result[k] = v.name
                    else:
                        result[k] = v
            return result
        else:
            # If not a model object, return as is
            return obj

    def _transaction_to_dict(self, transaction) -> Dict[str, Any]:
        """Convert a transaction model to a dictionary.

        Args:
            transaction: Transaction model to convert

        Returns:
            Dictionary representation of the transaction
        """
        return {
            'id': transaction.id,
            'type': transaction.type.name if hasattr(transaction.type, 'name') else str(transaction.type),
            'quantity': transaction.quantity,
            'date': transaction.created_at.isoformat() if hasattr(transaction,
                                                                  'created_at') and transaction.created_at else None,
            'notes': getattr(transaction, 'notes', None)
        }