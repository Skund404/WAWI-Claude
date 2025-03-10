# services/implementations/product_service.py
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database.models.product import Product
from database.models.pattern import Pattern
from database.models.inventory import Inventory
from database.models.enums import InventoryStatus, TransactionType
from database.repositories.product_repository import ProductRepository
from database.repositories.pattern_repository import PatternRepository
from database.repositories.inventory_repository import InventoryRepository
from database.repositories.sales_item_repository import SalesItemRepository

from services.base_service import BaseService, ValidationError, NotFoundError, ServiceError
from services.interfaces.product_service import IProductService

from di.core import inject


class ProductService(BaseService, IProductService):
    """Implementation of the Product Service interface.

    This service provides functionality for managing products in the leatherworking
    application, including catalog management, pricing, and inventory tracking.
    """

    @inject
    def __init__(self,
                 session: Session,
                 product_repository: Optional[ProductRepository] = None,
                 pattern_repository: Optional[PatternRepository] = None,
                 inventory_repository: Optional[InventoryRepository] = None,
                 sales_item_repository: Optional[SalesItemRepository] = None):
        """Initialize the Product Service.

        Args:
            session: SQLAlchemy database session
            product_repository: Optional ProductRepository instance
            pattern_repository: Optional PatternRepository instance
            inventory_repository: Optional InventoryRepository instance
            sales_item_repository: Optional SalesItemRepository instance
        """
        super().__init__(session)
        self.product_repository = product_repository or ProductRepository(session)
        self.pattern_repository = pattern_repository or PatternRepository(session)
        self.inventory_repository = inventory_repository or InventoryRepository(session)
        self.sales_item_repository = sales_item_repository or SalesItemRepository(session)
        self.logger = logging.getLogger(__name__)

    def get_by_id(self, product_id: int) -> Dict[str, Any]:
        """Retrieve a product by its ID.

        Args:
            product_id: The ID of the product to retrieve

        Returns:
            A dictionary representation of the product

        Raises:
            NotFoundError: If the product does not exist
        """
        try:
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")
            return self._to_dict(product)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error retrieving product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to retrieve product: {str(e)}")

    def get_all(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Retrieve all products with optional filtering.

        Args:
            filters: Optional filters to apply to the product query

        Returns:
            List of dictionaries representing products
        """
        try:
            products = self.product_repository.get_all(filters)
            return [self._to_dict(product) for product in products]
        except Exception as e:
            self.logger.error(f"Error retrieving products: {str(e)}")
            raise ServiceError(f"Failed to retrieve products: {str(e)}")

    def create(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product.

        Args:
            product_data: Dictionary containing product data

        Returns:
            Dictionary representation of the created product

        Raises:
            ValidationError: If the product data is invalid
        """
        try:
            # Validate the product data
            self._validate_product_data(product_data)

            # Get pattern if pattern_id is provided
            if 'pattern_id' in product_data:
                pattern_id = product_data.pop('pattern_id')
                pattern = self.pattern_repository.get_by_id(pattern_id)
                if not pattern:
                    raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Create the product within a transaction
            with self.transaction():
                product = Product(**product_data)
                created_product = self.product_repository.create(product)

                # Link pattern if provided
                if 'pattern_id' in locals():
                    self.product_repository.link_pattern(created_product.id, pattern_id)

                # Create inventory entry for the product if initial_quantity is provided
                if 'initial_quantity' in product_data:
                    initial_quantity = product_data.get('initial_quantity', 0)
                    inventory_data = {
                        'item_type': 'product',
                        'item_id': created_product.id,
                        'quantity': initial_quantity,
                        'status': InventoryStatus.IN_STOCK.value,
                        'storage_location': product_data.get('storage_location', '')
                    }
                    self.inventory_repository.create(inventory_data)

                return self._to_dict(created_product)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error creating product: {str(e)}")
            raise ServiceError(f"Failed to create product: {str(e)}")

    def update(self, product_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product.

        Args:
            product_id: ID of the product to update
            product_data: Dictionary containing updated product data

        Returns:
            Dictionary representation of the updated product

        Raises:
            NotFoundError: If the product does not exist
            ValidationError: If the updated data is invalid
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Validate product data
            self._validate_product_data(product_data, update=True)

            # Handle pattern linking separately if pattern_id is provided
            pattern_id = None
            if 'pattern_id' in product_data:
                pattern_id = product_data.pop('pattern_id')
                pattern = self.pattern_repository.get_by_id(pattern_id)
                if not pattern:
                    raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Update the product within a transaction
            with self.transaction():
                updated_product = self.product_repository.update(product_id, product_data)

                # Link pattern if provided
                if pattern_id is not None:
                    self.product_repository.link_pattern(product_id, pattern_id)

                return self._to_dict(updated_product)
        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to update product: {str(e)}")

    def delete(self, product_id: int) -> bool:
        """Delete a product by its ID.

        Args:
            product_id: ID of the product to delete

        Returns:
            True if the product was successfully deleted

        Raises:
            NotFoundError: If the product does not exist
            ServiceError: If the product cannot be deleted (e.g., in use)
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Check if product has sales history
            sales_items = self.sales_item_repository.get_by_product(product_id)
            if sales_items and len(sales_items) > 0:
                raise ServiceError(f"Cannot delete product {product_id} as it has sales history")

            # Delete the product within a transaction
            with self.transaction():
                # First remove pattern links
                self.product_repository.unlink_all_patterns(product_id)

                # Remove inventory entries
                inventory_entries = self.inventory_repository.get_by_item(item_type='product', item_id=product_id)
                for entry in inventory_entries:
                    self.inventory_repository.delete(entry.id)

                # Then delete the product
                self.product_repository.delete(product_id)
                return True
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error deleting product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to delete product: {str(e)}")

    def find_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Find products by name (partial match).

        Args:
            name: Name or partial name to search for

        Returns:
            List of dictionaries representing matching products
        """
        try:
            products = self.product_repository.find_by_name(name)
            return [self._to_dict(product) for product in products]
        except Exception as e:
            self.logger.error(f"Error finding products by name '{name}': {str(e)}")
            raise ServiceError(f"Failed to find products by name: {str(e)}")

    def get_by_pattern(self, pattern_id: int) -> List[Dict[str, Any]]:
        """Find products that use a specific pattern.

        Args:
            pattern_id: ID of the pattern

        Returns:
            List of dictionaries representing products using the pattern

        Raises:
            NotFoundError: If the pattern does not exist
        """
        try:
            # Verify pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Get products using the pattern
            products = self.product_repository.get_by_pattern(pattern_id)
            return [self._to_dict(product) for product in products]
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error finding products by pattern {pattern_id}: {str(e)}")
            raise ServiceError(f"Failed to find products by pattern: {str(e)}")

    def link_pattern(self, product_id: int, pattern_id: int) -> Dict[str, Any]:
        """Link a pattern to a product.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern

        Returns:
            Dictionary representation of the updated product

        Raises:
            NotFoundError: If the product or pattern does not exist
            ValidationError: If the pattern is already linked to the product
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Verify pattern exists
            pattern = self.pattern_repository.get_by_id(pattern_id)
            if not pattern:
                raise NotFoundError(f"Pattern with ID {pattern_id} not found")

            # Link pattern to product within a transaction
            with self.transaction():
                # Check if already linked
                existing_links = self.product_repository.get_patterns(product_id)
                if any(p.id == pattern_id for p in existing_links):
                    raise ValidationError(f"Pattern {pattern_id} is already linked to product {product_id}")

                self.product_repository.link_pattern(product_id, pattern_id)

                # Get updated product
                updated_product = self.product_repository.get_by_id(product_id)
                return self._to_dict(updated_product)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error linking pattern {pattern_id} to product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to link pattern to product: {str(e)}")

    def unlink_pattern(self, product_id: int, pattern_id: int) -> bool:
        """Unlink a pattern from a product.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern

        Returns:
            True if the pattern was successfully unlinked

        Raises:
            NotFoundError: If the product or the product-pattern link does not exist
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Check if link exists
            existing_links = self.product_repository.get_patterns(product_id)
            if not any(p.id == pattern_id for p in existing_links):
                raise NotFoundError(f"Pattern {pattern_id} is not linked to product {product_id}")

            # Unlink pattern from product within a transaction
            with self.transaction():
                self.product_repository.unlink_pattern(product_id, pattern_id)
                return True
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error unlinking pattern {pattern_id} from product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to unlink pattern from product: {str(e)}")

    def update_inventory(self, product_id: int, quantity: int, notes: str = None) -> Dict[str, Any]:
        """Update the inventory of a product.

        Args:
            product_id: ID of the product
            quantity: Quantity to adjust (positive or negative)
            notes: Optional notes about the adjustment

        Returns:
            Dictionary containing updated inventory information

        Raises:
            NotFoundError: If the product does not exist
            ValidationError: If the adjustment would result in negative inventory
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Get inventory entry
            inventory_entries = self.inventory_repository.get_by_item(item_type='product', item_id=product_id)

            if not inventory_entries:
                # If no inventory entry exists and quantity is positive, create one
                if quantity <= 0:
                    raise ValidationError(f"Cannot adjust inventory by {quantity} when no inventory exists")

                with self.transaction():
                    inventory_data = {
                        'item_type': 'product',
                        'item_id': product_id,
                        'quantity': quantity,
                        'status': InventoryStatus.IN_STOCK.value,
                        'storage_location': '',
                        'notes': notes
                    }
                    inventory = self.inventory_repository.create(inventory_data)
                    return self._to_dict(inventory)
            else:
                # Use the first inventory entry (should be only one per product)
                inventory = inventory_entries[0]

                # Check if adjustment would result in negative inventory
                if inventory.quantity + quantity < 0:
                    raise ValidationError(
                        f"Cannot reduce inventory below zero (current: {inventory.quantity}, adjustment: {quantity})")

                # Update inventory within a transaction
                with self.transaction():
                    # Determine transaction type
                    transaction_type = TransactionType.USAGE.value if quantity < 0 else TransactionType.RESTOCK.value

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
                    if notes:
                        inventory_data['notes'] = notes

                    updated_inventory = self.inventory_repository.update(inventory.id, inventory_data)

                    # Create transaction record if available
                    if hasattr(self, 'transaction_repository'):
                        transaction_data = {
                            'item_type': 'product',
                            'item_id': product_id,
                            'quantity': abs(quantity),
                            'type': transaction_type,
                            'notes': notes or f"Inventory adjustment: {quantity}"
                        }
                        self.transaction_repository.create(transaction_data)

                    return self._to_dict(updated_inventory)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating inventory for product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to update inventory: {str(e)}")

    def get_inventory_status(self, product_id: int) -> Dict[str, Any]:
        """Get the current inventory status of a product.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary containing inventory information

        Raises:
            NotFoundError: If the product does not exist
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Get inventory entry
            inventory_entries = self.inventory_repository.get_by_item(item_type='product', item_id=product_id)

            if not inventory_entries:
                return {
                    'product_id': product_id,
                    'quantity': 0,
                    'status': InventoryStatus.OUT_OF_STOCK.value,
                    'storage_location': '',
                    'last_updated': None
                }
            else:
                # Use the first inventory entry (should be only one per product)
                inventory = inventory_entries[0]
                return self._to_dict(inventory)
        except NotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting inventory status for product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to get inventory status: {str(e)}")

    def calculate_production_cost(self, product_id: int) -> Dict[str, float]:
        """Calculate the production cost of a product based on its pattern and materials.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with cost breakdown (materials, labor, overhead, total)

        Raises:
            NotFoundError: If the product does not exist
            ServiceError: If the product is not linked to a pattern
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Get patterns linked to the product
            patterns = self.product_repository.get_patterns(product_id)
            if not patterns:
                raise ServiceError(f"Product {product_id} is not linked to any pattern")

            # Use the first pattern (assuming products typically use one pattern)
            pattern = patterns[0]

            # Initialize cost components
            material_cost = 0.0
            labor_cost = 0.0
            overhead_cost = 0.0

            # Calculate material costs based on pattern components
            components = self.pattern_repository.get_components(pattern.id)
            for component in components:
                # Get materials for this component
                component_materials = self.pattern_repository.get_component_materials(component.id)

                for cm in component_materials:
                    material = cm.material
                    # Calculate material cost
                    unit_cost = getattr(material, 'unit_cost', 0.0)
                    material_cost += unit_cost * cm.quantity

            # Calculate labor cost based on pattern complexity
            skill_level_multipliers = {
                'BEGINNER': 1.0,
                'INTERMEDIATE': 1.5,
                'ADVANCED': 2.0,
                'EXPERT': 3.0
            }

            # Get skill level from pattern if available
            skill_level = getattr(pattern, 'skill_level', None)
            skill_multiplier = skill_level_multipliers.get(
                skill_level.name if hasattr(skill_level, 'name') else 'INTERMEDIATE',
                1.5
            )

            # Base labor rate (could be configurable)
            base_labor_rate = 20.0  # Per hour
            estimated_hours = 2.0  # Default estimate

            # Adjust estimated hours based on component count
            if len(components) > 10:
                estimated_hours = 4.0
            elif len(components) > 5:
                estimated_hours = 3.0

            labor_cost = base_labor_rate * estimated_hours * skill_multiplier

            # Calculate overhead (typically a percentage of material + labor)
            overhead_rate = 0.15  # 15% overhead
            overhead_cost = (material_cost + labor_cost) * overhead_rate

            # Calculate total cost
            total_cost = material_cost + labor_cost + overhead_cost

            return {
                'material_cost': round(material_cost, 2),
                'labor_cost': round(labor_cost, 2),
                'overhead_cost': round(overhead_cost, 2),
                'total_cost': round(total_cost, 2),
                'estimated_hours': estimated_hours,
                'skill_level': skill_level.name if hasattr(skill_level, 'name') else 'INTERMEDIATE'
            }
        except (NotFoundError, ServiceError):
            raise
        except Exception as e:
            self.logger.error(f"Error calculating production cost for product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to calculate production cost: {str(e)}")

    def update_pricing(self, product_id: int, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update the pricing information for a product.

        Args:
            product_id: ID of the product
            pricing_data: Dictionary containing pricing information

        Returns:
            Dictionary representation of the updated product

        Raises:
            NotFoundError: If the product does not exist
            ValidationError: If the pricing data is invalid
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

            # Validate pricing data
            self._validate_pricing_data(pricing_data)

            # Update product pricing within a transaction
            with self.transaction():
                update_data = {}

                if 'price' in pricing_data:
                    update_data['price'] = pricing_data['price']

                if 'wholesale_price' in pricing_data:
                    update_data['wholesale_price'] = pricing_data['wholesale_price']

                if 'sale_price' in pricing_data:
                    update_data['sale_price'] = pricing_data['sale_price']

                if 'cost' in pricing_data:
                    update_data['cost'] = pricing_data['cost']

                if 'markup_percentage' in pricing_data:
                    update_data['markup_percentage'] = pricing_data['markup_percentage']

                if 'tax_rate' in pricing_data:
                    update_data['tax_rate'] = pricing_data['tax_rate']

                updated_product = self.product_repository.update(product_id, update_data)
                return self._to_dict(updated_product)
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error updating pricing for product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to update pricing: {str(e)}")

    def get_sales_history(self, product_id: int,
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get the sales history for a product.

        Args:
            product_id: ID of the product
            start_date: Optional start date (ISO format)
            end_date: Optional end date (ISO format)

        Returns:
            List of dictionaries containing sales information

        Raises:
            NotFoundError: If the product does not exist
        """
        try:
            # Verify product exists
            product = self.product_repository.get_by_id(product_id)
            if not product:
                raise NotFoundError(f"Product with ID {product_id} not found")

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

            # Get sales history
            sales_items = self.sales_item_repository.get_by_product(
                product_id,
                start_date=start_datetime,
                end_date=end_datetime
            )

            result = []
            for item in sales_items:
                # Get related sale
                sale = item.sale if hasattr(item, 'sale') else None

                sale_dict = {
                    'sales_item_id': item.id,
                    'sale_id': getattr(sale, 'id', None),
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': item.quantity * item.price,
                    'sale_date': getattr(sale, 'created_at', None),
                    'sale_status': getattr(sale, 'status', None)
                }

                result.append(sale_dict)

            return result
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self.logger.error(f"Error getting sales history for product {product_id}: {str(e)}")
            raise ServiceError(f"Failed to get sales history: {str(e)}")

    def _validate_product_data(self, data: Dict[str, Any], update: bool = False) -> None:
        """Validate product data.

        Args:
            data: Product data to validate
            update: Whether this is an update operation

        Raises:
            ValidationError: If validation fails
        """
        # Required fields for new products
        if not update:
            required_fields = ['name']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing required field: {field}")

        # Validate price if provided
        if 'price' in data:
            try:
                price = float(data['price'])
                if price < 0:
                    raise ValidationError("Price cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Price must be a valid number")

        # Validate initial_quantity if provided
        if 'initial_quantity' in data:
            try:
                quantity = int(data['initial_quantity'])
                if quantity < 0:
                    raise ValidationError("Initial quantity cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Initial quantity must be a valid integer")

    def _validate_pricing_data(self, data: Dict[str, Any]) -> None:
        """Validate pricing data.

        Args:
            data: Pricing data to validate

        Raises:
            ValidationError: If validation fails
        """
        if not data:
            raise ValidationError("Pricing data cannot be empty")

        price_fields = ['price', 'wholesale_price', 'sale_price', 'cost']
        for field in price_fields:
            if field in data:
                try:
                    value = float(data[field])
                    if value < 0:
                        raise ValidationError(f"{field} cannot be negative")
                except (ValueError, TypeError):
                    raise ValidationError(f"{field} must be a valid number")

        if 'markup_percentage' in data:
            try:
                markup = float(data['markup_percentage'])
                if markup < 0:
                    raise ValidationError("Markup percentage cannot be negative")
            except (ValueError, TypeError):
                raise ValidationError("Markup percentage must be a valid number")

        if 'tax_rate' in data:
            try:
                tax_rate = float(data['tax_rate'])
                if tax_rate < 0 or tax_rate > 100:
                    raise ValidationError("Tax rate must be between 0 and 100")
            except (ValueError, TypeError):
                raise ValidationError("Tax rate must be a valid number")

    def _to_dict(self, obj) -> Dict[str, Any]:
        """Convert a model object to a dictionary representation.

        Args:
            obj: Model object to convert

        Returns:
            Dictionary representation of the object
        """
        if isinstance(obj, Product):
            result = {
                'id': obj.id,
                'name': obj.name,
                'description': getattr(obj, 'description', None),
                'price': getattr(obj, 'price', None),
                'created_at': obj.created_at.isoformat() if hasattr(obj, 'created_at') and obj.created_at else None,
                'updated_at': obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None,
            }

            # Include other fields if present
            optional_fields = [
                'sku', 'upc', 'wholesale_price', 'sale_price', 'cost',
                'markup_percentage', 'tax_rate', 'is_active'
            ]

            for field in optional_fields:
                if hasattr(obj, field):
                    result[field] = getattr(obj, field)

            return result
        elif isinstance(obj, Inventory):
            result = {
                'id': obj.id,
                'item_type': obj.item_type,
                'item_id': obj.item_id,
                'quantity': obj.quantity,
                'status': obj.status.name if hasattr(obj, 'status') and hasattr(obj.status, 'name') else str(
                    obj.status),
                'storage_location': getattr(obj, 'storage_location', None),
                'last_updated': obj.updated_at.isoformat() if hasattr(obj, 'updated_at') and obj.updated_at else None,
            }

            return result
        elif hasattr(obj, '__dict__'):
            # Generic conversion for other model types
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        else:
            # If not a model object, return as is
            return obj