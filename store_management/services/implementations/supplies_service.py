# services/implementations/supplies_service.py
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.material import Supplies
from database.models.enums import MaterialType, InventoryStatus
from database.repositories.supplies_repository import SuppliesRepository
from database.repositories.component_repository import ComponentRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.supplier_repository import SupplierRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.implementations.material_service import MaterialService
from services.interfaces.supplies_service import ISuppliesService

from di.core import inject


class SuppliesService(MaterialService, ISuppliesService):
    """Implementation of the Supplies Service interface.

    This service provides specialized functionality for managing consumable supplies
    used in leatherworking, such as thread, adhesives, dyes, and finishes.
    """

    @inject
    def __init__(self,
                 session: Session,
                 supplies_repository: Optional[SuppliesRepository] = None,
                 component_repository: Optional[ComponentRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None,
                 supplier_repository: Optional[SupplierRepository] = None):
        """Initialize the Supplies Service.

        Args:
            session: SQLAlchemy database session
            supplies_repository: Optional SuppliesRepository instance
            component_repository: Optional ComponentRepository instance
            inventory_repository: Optional InventoryRepository instance
            supplier_repository: Optional SupplierRepository instance
        """
        super().__init__(session)
        self.supplies_repository = supplies_repository or SuppliesRepository(session)
        self.component_repository = component_repository or ComponentRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.supplier_repository = supplier_repository or SupplierRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, supply_id: int) -> Dict[str, Any]:
        """Retrieve a supply item by its ID.

        Args:
            supply_id: The ID of the supply to retrieve

        Returns:
            A dictionary representation of the supply

        Raises:
            NotFoundError: If the supply does not exist
        """
        try:
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")
            return self._to_dict(supply)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve supply: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all supplies with optional filtering.

        Args:
            filters: Optional filters to apply to the supply query

        Returns:
            List of dictionaries representing supplies
        """
        try:
            supplies = self.supplies_repository.get_all(filters)
            return [self._to_dict(supply) for supply in supplies]
        except Exception as e:
            self.logger.error(f"Error retrieving supplies: {str(e)}")
            raise ServiceError(f"Failed to retrieve supplies: {str(e)}")

    def create(self, supply_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supply item.

        Args:
            supply_data: Dictionary containing supply data

        Returns:
            Dictionary representation of the created supply

        Raises:
            ValidationError: If the supply data is invalid
        """
        try:
            # Validate the supply data
            self._validate_supply_data(supply_data)

            # Set material_type based on supply_type if provided
            if 'supply_type' in supply_data:
                if supply_data['supply_type'] == 'THREAD':
                    supply_data['material_type'] = 'THREAD'
                elif supply_data['supply_type'] == 'ADHESIVE':
                    supply_data['material_type'] = 'ADHESIVE'
                elif supply_data['supply_type'] == 'DYE':
                    supply_data['material_type'] = 'DYE'
                elif supply_data['supply_type'] == 'FINISH':
                    supply_data['material_type'] = 'FINISH'
                elif supply_data['supply_type'] == 'EDGE_PAINT':
                    supply_data['material_type'] = 'EDGE_PAINT'
                else:
                    supply_data['material_type'] = 'SUPPLIES'
            else:
                supply_data['material_type'] = 'SUPPLIES'

            # Check supplier if supplier_id is provided
            if 'supplier_id' in supply_data and supply_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(supply_data['supplier_id'])
                if not supplier:
                    raise NotFoundError(f"Supplier with ID {supply_data['supplier_id']} not found")

            # Create the supply within a transaction
            with self.transaction():
                supply = Supplies(**supply_data)
                created_supply = self.supplies_repository.create(supply)

                # Create inventory entry for the supply if initial_quantity is provided
                if 'initial_quantity' in supply_data:
                    initial_quantity = supply_data.get('initial_quantity', 0)
                    inventory_data = {
                        'item_type': 'material',
                        'item_id': created_supply.id,
                        'quantity': initial_quantity,
                        'status': InventoryStatus.IN_STOCK.value if initial_quantity > 0 else InventoryStatus.OUT_OF_STOCK.value,
                        'storage_location': supply_data.get('storage_location', '')
                    }
                    self.inventory_repository.create(inventory_data)

                return self._to_dict(created_supply)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating supply: {str(e)}")
            raise ServiceError(f"Failed to create supply: {str(e)}")

    def update(self, supply_id: int, supply_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supply item.

        Args:
            supply_id: ID of the supply to update
            supply_data: Dictionary containing updated supply data

        Returns:
            Dictionary representation of the updated supply

        Raises:
            NotFoundError: If the supply does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Validate supply data
            self._validate_supply_data(supply_data, update=True)

            # Check supplier if supplier_id is provided
            if 'supplier_id' in supply_data and supply_data['supplier_id']:
                supplier = self.supplier_repository.get_by_id(supply_data['supplier_id'])
                if not supplier:
                    raise NotFoundError(f"Supplier with ID {supply_data['supplier_id']} not found")

            # Update the supply within a transaction
            with self.transaction():
                updated_supply = self.supplies_repository.update(supply_id, supply_data)
                return self._to_dict(updated_supply)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to update supply: {str(e)}")

    def delete(self, supply_id: int) -> bool:
        """Delete a supply item by its ID.

        Args:
            supply_id: ID of the supply to delete

        Returns:
            True if the supply was successfully deleted

        Raises:
            NotFoundError: If the supply does not exist
            ServiceError: If the supply cannot be deleted (e.g., in use)
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Check if supply is used in any components
            components_using = self.get_components_using(supply_id)
            if components_using:
                raise ServiceError(
                    f"Cannot delete supply {supply_id} as it is used in {len(components_using)} components")

            # Delete the supply within a transaction
            with self.transaction():
                # Delete inventory entries first
                inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=supply_id)
                for entry in inventory_entries:
                    self.inventory_repository.delete(entry.id)

                # Then delete the supply
                self.supplies_repository.delete(supply_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to delete supply: {str(e)}")

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find supplies by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching supplies
        """
        try:
            supplies = self.supplies_repository.find_by_name(name)
            return [self._to_dict(supply) for supply in supplies]
        except Exception as e:
            self.logger.error(f"Error finding supplies by name '{name}': {str(e)}")
            raise ServiceError(f"Failed to find supplies by name: {str(e)}")

    def find_by_type(self, supply_type: str) -> List[Dict[str, Any]]:
        """Find supplies by type.

        Args:
            supply_type: Supply type to filter by

        Returns:
            List of dictionaries representing supplies of the specified type
        """
        try:
            # Validate supply type
            self._validate_supply_type(supply_type)

            supplies = self.supplies_repository.find_by_type(supply_type)
            return [self._to_dict(supply) for supply in supplies]
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding supplies by type '{supply_type}': {str(e)}")
            raise ServiceError(f"Failed to find supplies by type: {str(e)}")

    def find_by_color(self, color: str) -> List[Dict[str, Any]]:
        """Find supplies by color.

        Args:
            color: Color to filter by

        Returns:
            List of dictionaries representing supplies of the specified color
        """
        try:
            supplies = self.supplies_repository.find_by_color(color)
            return [self._to_dict(supply) for supply in supplies]
        except Exception as e:
            self.logger.error(f"Error finding supplies by color '{color}': {str(e)}")
            raise ServiceError(f"Failed to find supplies by color: {str(e)}")

    def get_by_supplier(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Find supplies provided by a specific supplier.

        Args:
            supplier_id: ID of the supplier

        Returns:
            List of dictionaries representing supplies from the supplier

        Raises:
            NotFoundError: If the supplier does not exist
        """
        try:
            # Verify supplier exists
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if not supplier:
                raise NotFoundError(f"Supplier with ID {supplier_id} not found")

            supplies = self.supplies_repository.get_by_supplier(supplier_id)
            return [self._to_dict(supply) for supply in supplies]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding supplies by supplier {supplier_id}: {str(e)}")
            raise ServiceError(f"Failed to find supplies by supplier: {str(e)}")

    def get_inventory_status(self, supply_id: int) -> Dict[str, Any]:
        """Get the current inventory status of a supply item.

        Args:
            supply_id: ID of the supply

        Returns:
            Dictionary containing inventory information

        Raises:
            NotFoundError: If the supply does not exist
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Get inventory entry
            inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=supply_id)

            if not inventory_entries:
                return {
                    'supply_id': supply_id,
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': '',
                    'last_updated': None
                }
            else:
                # Use the first inventory entry (should be only one per supply)
                inventory = inventory_entries[0]
                return {
                    'supply_id': supply_id,
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
            self.logger.error(f"Error getting inventory status for supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to get inventory status: {str(e)}")

    def adjust_inventory(self, supply_id: int,
                         quantity: float,
                         reason: str) -> Dict[str, Any]:
        """Adjust the inventory of a supply item.

        Args:
            supply_id: ID of the supply
            quantity: Quantity to adjust (positive or negative)
            reason: Reason for the adjustment

        Returns:
            Dictionary containing updated inventory information

        Raises:
            NotFoundError: If the supply does not exist
            ValidationError: If the adjustment would result in negative inventory
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Get inventory entry
            inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=supply_id)

            if not inventory_entries:
                # If no inventory entry exists and quantity is positive, create one
                if quantity <= 0:
                    raise ValidationError(f"Cannot adjust inventory by {quantity} when no inventory exists")

                with self.transaction():
                    inventory_data = {
                        'item_type': 'material',
                        'item_id': supply_id,
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
                            'item_id': supply_id,
                            'quantity': abs(quantity),
                            'type': 'RESTOCK',
                            'notes': reason
                        }
                        self.transaction_repository.create(transaction_data)

                    return {
                        'supply_id': supply_id,
                        'inventory_id': inventory.id,
                        'quantity': inventory.quantity,
                        'status': inventory.status.name if hasattr(inventory.status, 'name') else str(inventory.status),
                        'storage_location': getattr(inventory, 'storage_location', ''),
                        'last_updated': inventory.updated_at.isoformat() if hasattr(inventory,
                                                                                    'updated_at') and inventory.updated_at else None
                    }
            else:
                # Use the first inventory entry (should be only one per supply)
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
                    elif new_quantity < supply.reorder_threshold if hasattr(supply, 'reorder_threshold') else 5:
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
                            'item_id': supply_id,
                            'quantity': abs(quantity),
                            'type': transaction_type,
                            'notes': reason
                        }
                        self.transaction_repository.create(transaction_data)

                    return {
                        'supply_id': supply_id,
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
            self.logger.error(f"Error adjusting inventory for supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to adjust inventory: {str(e)}")

    def get_components_using(self, supply_id: int) -> List[Dict[str, Any]]:
        """Get components that use a specific supply item.

        Args:
            supply_id: ID of the supply

        Returns:
            List of dictionaries representing components that use the supply

        Raises:
            NotFoundError: If the supply does not exist
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Get components using the supply
            components_with_qty = self.component_repository.get_components_using_material(supply_id)

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
            self.logger.error(f"Error getting components using supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to get components using supply: {str(e)}")

    def get_usage_history(self, supply_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the usage history for a supply item.

        Args:
            supply_id: ID of the supply
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            List of dictionaries containing usage records

        Raises:
            NotFoundError: If the supply does not exist
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

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
                item_id=supply_id,
                start_date=start_datetime,
                end_date=end_datetime
            )

            return [self._transaction_to_dict(transaction) for transaction in transactions]
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error getting usage history for supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to get usage history: {str(e)}")

    def calculate_usage_rate(self, supply_id: int,
                             period_days: int = 30) -> Dict[str, Any]:
        """Calculate the usage rate of a supply item.

        Args:
            supply_id: ID of the supply
            period_days: Number of days to analyze

        Returns:
            Dictionary containing usage rate information

        Raises:
            NotFoundError: If the supply does not exist
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Check if transaction repository is available
            if not hasattr(self, 'transaction_repository'):
                return {
                    'supply_id': supply_id,
                    'average_daily_usage': 0,
                    'average_weekly_usage': 0,
                    'average_monthly_usage': 0,
                    'total_usage': 0,
                    'period_days': period_days,
                    'note': "Usage rate calculation requires transaction history"
                }

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)

            # Get usage transactions
            transactions = self.transaction_repository.get_by_item(
                item_type='material',
                item_id=supply_id,
                start_date=start_date,
                end_date=end_date,
                transaction_type='USAGE'
            )

            # Calculate total usage
            total_usage = sum(transaction.quantity for transaction in transactions)

            # Calculate average rates
            if period_days > 0:
                average_daily_usage = total_usage / period_days
                average_weekly_usage = average_daily_usage * 7
                average_monthly_usage = average_daily_usage * 30
            else:
                average_daily_usage = 0
                average_weekly_usage = 0
                average_monthly_usage = 0

            # Get current inventory
            inventory = self.get_inventory_status(supply_id)
            current_quantity = inventory.get('quantity', 0)

            # Calculate days until empty if average daily usage > 0
            days_until_empty = None
            if average_daily_usage > 0:
                days_until_empty = current_quantity / average_daily_usage

            return {
                'supply_id': supply_id,
                'average_daily_usage': round(average_daily_usage, 2),
                'average_weekly_usage': round(average_weekly_usage, 2),
                'average_monthly_usage': round(average_monthly_usage, 2),
                'total_usage': total_usage,
                'period_days': period_days,
                'current_quantity': current_quantity,
                'days_until_empty': round(days_until_empty, 1) if days_until_empty is not None else None
            }
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error calculating usage rate for supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to calculate usage rate: {str(e)}")

    def get_low_stock_supplies(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """Get supplies that are low in stock.

        Args:
            threshold: Optional threshold percentage (0-100)

        Returns:
            List of dictionaries representing low stock supplies
        """
        try:
            # Default threshold is 20% if not specified
            threshold_percent = threshold if threshold is not None else 20

            # Get all supplies
            all_supplies = self.supplies_repository.get_all()
            result = []

            for supply in all_supplies:
                # Get inventory status
                inventory_entries = self.inventory_repository.get_by_item(item_type='material', item_id=supply.id)

                if not inventory_entries:
                    # No inventory record, consider as out of stock
                    supply_dict = self._to_dict(supply)
                    supply_dict['quantity'] = 0
                    supply_dict['status'] = InventoryStatus.OUT_OF_STOCK.value
                    supply_dict['threshold_percent'] = threshold_percent
                    result.append(supply_dict)
                else:
                    inventory = inventory_entries[0]
                    current_quantity = inventory.quantity

                    # Get reorder threshold or use a default (5)
                    reorder_threshold = getattr(supply, 'reorder_threshold', 5)

                    # Check if quantity is below threshold
                    if current_quantity <= reorder_threshold:
                        supply_dict = self._to_dict(supply)
                        supply_dict['quantity'] = current_quantity
                        supply_dict['status'] = inventory.status.name if hasattr(inventory.status, 'name') else str(
                            inventory.status)
                        supply_dict['threshold_percent'] = threshold_percent
                        supply_dict['reorder_threshold'] = reorder_threshold
                        result.append(supply_dict)
                    elif hasattr(supply, 'par_level') and supply.par_level > 0:
                        # Calculate percentage of PAR level
                        par_percent = (current_quantity / supply.par_level) * 100
                        if par_percent <= threshold_percent:
                            supply_dict = self._to_dict(supply)
                            supply_dict['quantity'] = current_quantity
                            supply_dict['status'] = inventory.status.name if hasattr(inventory.status, 'name') else str(
                                inventory.status)
                            supply_dict['threshold_percent'] = threshold_percent
                            supply_dict['par_level'] = supply.par_level
                            supply_dict['par_percent'] = round(par_percent, 1)
                            result.append(supply_dict)

            return result
        except Exception as e:
            self.logger.error(f"Error getting low stock supplies: {str(e)}")
            raise ServiceError(f"Failed to get low stock supplies: {str(e)}")

    def get_reorder_recommendations(self) -> List[Dict[str, Any]]:
        """Get recommendations for supplies that should be reordered.

        Returns:
            List of dictionaries representing supplies that should be reordered
        """
        try:
            # Get low stock supplies as a starting point
            low_stock_supplies = self.get_low_stock_supplies()

            # For each supply, calculate usage rate and days until empty
            result = []

            for supply_info in low_stock_supplies:
                supply_id = supply_info['id']

                try:
                    # Calculate usage rate for the last 90 days
                    usage_info = self.calculate_usage_rate(supply_id, period_days=90)

                    # Combine information
                    recommendation = {**supply_info, **usage_info}

                    # Calculate recommended order quantity
                    min_order_quantity = getattr(supply_info, 'minimum_order_quantity', 1)

                    if 'average_monthly_usage' in usage_info and usage_info['average_monthly_usage'] > 0:
                        # Base order on 2 months of usage or minimum order quantity, whichever is higher
                        recommended_quantity = max(
                            min_order_quantity,
                            round(usage_info['average_monthly_usage'] * 2)
                        )
                        recommendation['recommended_order_quantity'] = recommended_quantity
                    else:
                        # No usage data, use reorder threshold or minimum order quantity
                        reorder_amount = max(
                            min_order_quantity,
                            supply_info.get('reorder_threshold', 5)
                        )
                        recommendation['recommended_order_quantity'] = reorder_amount

                    # Add urgency level
                    if supply_info.get('quantity', 0) == 0:
                        recommendation['urgency'] = 'HIGH'
                    elif 'days_until_empty' in usage_info and usage_info['days_until_empty'] is not None:
                        if usage_info['days_until_empty'] < 7:
                            recommendation['urgency'] = 'HIGH'
                        elif usage_info['days_until_empty'] < 14:
                            recommendation['urgency'] = 'MEDIUM'
                        else:
                            recommendation['urgency'] = 'LOW'
                    else:
                        recommendation['urgency'] = 'MEDIUM'

                    result.append(recommendation)
                except Exception as calc_error:
                    # Skip this supply if there's an error calculating usage rate
                    self.logger.warning(f"Error calculating usage rate for supply {supply_id}: {str(calc_error)}")
                    continue

            # Sort by urgency (HIGH, MEDIUM, LOW)
            urgency_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
            result.sort(key=lambda x: urgency_order.get(x.get('urgency', 'LOW'), 3))

            return result
        except Exception as e:
            self.logger.error(f"Error getting reorder recommendations: {str(e)}")
            raise ServiceError(f"Failed to get reorder recommendations: {str(e)}")

    def track_batch(self, supply_id: int,
                    batch_number: str,
                    batch_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track a specific batch of a supply item.

        Args:
            supply_id: ID of the supply
            batch_number: Batch number
            batch_data: Dictionary containing batch information

        Returns:
            Dictionary representing the tracked batch

        Raises:
            NotFoundError: If the supply does not exist
            ValidationError: If the batch data is invalid
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Validate batch data
            self._validate_batch_data(batch_data)

            # Check if batch repository is available
            if not hasattr(self, 'batch_repository'):
                # If no batch repository, store batch information in supply notes
                current_notes = getattr(supply, 'notes', '')
                batch_info = f"Batch {batch_number}: "
                for key, value in batch_data.items():
                    batch_info += f"{key}: {value}, "
                batch_info = batch_info.rstrip(', ')

                if current_notes:
                    updated_notes = f"{current_notes}\n{batch_info}"
                else:
                    updated_notes = batch_info

                with self.transaction():
                    self.supplies_repository.update(supply_id, {'notes': updated_notes})

                batch_result = {
                    'supply_id': supply_id,
                    'batch_number': batch_number
                }
                batch_result.update(batch_data)

                return batch_result
            else:
                # Add supply_id and batch_number to batch data
                batch_record_data = {
                    'supply_id': supply_id,
                    'batch_number': batch_number
                }
                batch_record_data.update(batch_data)

                # Create batch record
                with self.transaction():
                    batch_record = self.batch_repository.create(batch_record_data)
                    return self._to_dict(batch_record)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error tracking batch for supply {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to track batch: {str(e)}")

    def get_batch_info(self, supply_id: int, batch_number: str) -> Dict[str, Any]:
        """Get information about a specific batch of a supply item.

        Args:
            supply_id: ID of the supply
            batch_number: Batch number

        Returns:
            Dictionary containing batch information

        Raises:
            NotFoundError: If the supply or batch does not exist
        """
        try:
            # Verify supply exists
            supply = self.supplies_repository.get_by_id(supply_id)
            if not supply:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            # Check if batch repository is available
            if not hasattr(self, 'batch_repository'):
                # If no batch repository, try to extract batch information from supply notes
                if not hasattr(supply, 'notes') or not supply.notes:
                    raise NotFoundError(f"Batch {batch_number} not found for supply {supply_id}")

                # Simple parsing of batch information from notes
                batch_info = None
                for line in supply.notes.split('\n'):
                    if line.startswith(f"Batch {batch_number}:"):
                        batch_info = line.replace(f"Batch {batch_number}:", "").strip()
                        break

                if not batch_info:
                    raise NotFoundError(f"Batch {batch_number} not found for supply {supply_id}")

                # Parse batch info into dictionary
                batch_dict = {
                    'supply_id': supply_id,
                    'batch_number': batch_number
                }

                for item in batch_info.split(','):
                    if ':' in item:
                        key, value = item.split(':', 1)
                        batch_dict[key.strip()] = value.strip()

                return batch_dict
            else:
                # Get batch record from repository
                batch_record = self.batch_repository.get_by_supply_and_batch(supply_id, batch_number)
                if not batch_record:
                    raise NotFoundError(f"Batch {batch_number} not found for supply {supply_id}")

                return self._to_dict(batch_record)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting batch info for supply {supply_id}, batch {batch_number}: {str(e)}")
            raise ServiceError(f"Failed to get batch information: {str(e)}")

    def _validate_supply_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate supply data.

        Args:
            data: Supply data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for new supplies
        if not update:
            required_fields = ['name']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate supply type if provided
        if 'supply_type' in data:
            self._validate_supply_type(data['supply_type'])

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
                quantity = float(data['initial_quantity'])
                if quantity < 0:
                    raise ValidationError("Initial quantity cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Initial quantity must be a valid number")

        # Validate reorder_threshold if provided
        if 'reorder_threshold' in data:
            try:
                threshold = float(data['reorder_threshold'])
                if threshold < 0:
                    raise ValidationError("Reorder threshold cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Reorder threshold must be a valid number")

        # Validate par_level if provided
        if 'par_level' in data:
            try:
                par_level = float(data['par_level'])
                if par_level < 0:
                    raise ValidationError("PAR level cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("PAR level must be a valid number")

    def _validate_supply_type(self, supply_type: str) -> None:
        """Validate that the supply type is valid.

        Args:
            supply_type: Supply type to validate

        Raises:
            ValidationError: If the supply type is invalid
        """
        valid_types = ['THREAD', 'ADHESIVE', 'DYE', 'FINISH', 'EDGE_PAINT', 'WAX', 'CONDITIONER', 'SUPPLIES']
        if supply_type not in valid_types:
            raise ValidationError(f"Invalid supply type: {supply_type}. Valid types are: {valid_types}")

    def _validate_batch_data(self, data: Dict[str, Any]) -> None:
        """Validate batch data.

        Args:
            data: Batch data to validate

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for batch data
        required_fields = ['received_date']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")

        # Validate dates if provided
        date_fields = ['received_date', 'expiration_date', 'manufacture_date']
        for field in date_fields:
            if field in data and isinstance(data[field], str):
                try:
                    datetime.fromisoformat(data[field])
                except ValueError:
                    raise ValidationError(f"Invalid date format for {field}: {data[field]}. Use ISO format.")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, Supplies):
            result = {
                'id': obj.id,
                'name': obj.name,
                'material_type': obj.material_type.name if hasattr(obj.material_type, 'name') else str(
                    obj.material_type),
                'supply_type': getattr(obj, 'supply_type', None) or obj.material_type.name if hasattr(obj.material_type,
                                                                                                      'name') else None,
                'color': getattr(obj, 'color', None),
                'thickness': getattr(obj, 'thickness', None),
                'material_composition': getattr(obj, 'material_composition', None),
                'unit_cost': getattr(obj, 'unit_cost', None),
                'supplier_id': getattr(obj, 'supplier_id', None),
                'reorder_threshold': getattr(obj, 'reorder_threshold', None),
                'par_level': getattr(obj, 'par_level', None),
                'minimum_order_quantity': getattr(obj, 'minimum_order_quantity', None),
                'created_at': obj.created_at.isoformat() if hasattr(obj, 'created_at') and obj.created_at else None,
                'updated_at': obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None,
            }

            # Include other fields if present
            optional_fields = ['description', 'sku', 'unit', 'notes']

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