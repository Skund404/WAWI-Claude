# services/implementations/supplier_service.py
"""Implementation of the Supplier Service interface."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from services.base_service import BaseService, NotFoundError, ValidationError
from services.interfaces.supplier_service import ISupplierService, SupplierStatus


class SupplierService(BaseService, ISupplierService):
    """Concrete implementation of the Supplier Service interface.

    Provides operations for managing suppliers in the leatherworking application.
    """

    def __init__(self):
        """Initialize the supplier service."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._suppliers = {}
        self._supplier_products = {}
        self._supplier_orders = {}
        self._next_supplier_id = 1

        self.logger.info("SupplierService initialized")

    def get_all_suppliers(self) -> List[Dict[str, Any]]:
        """Get all suppliers.

        Returns:
            List[Dict[str, Any]]: List of all supplier data dictionaries
        """
        self.logger.info("Retrieving all suppliers")
        return list(self._suppliers.values())

    def get_supplier_by_id(self, supplier_id: int) -> Dict[str, Any]:
        """Get a supplier by its ID.

        Args:
            supplier_id (int): The supplier ID to retrieve

        Returns:
            Dict[str, Any]: Supplier data dictionary

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        self.logger.info(f"Retrieving supplier with ID {supplier_id}")

        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        return self._suppliers[supplier_id]

    def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier.

        Args:
            supplier_data (Dict[str, Any]): Supplier data to create

        Returns:
            Dict[str, Any]: Created supplier data

        Raises:
            ValidationError: If the supplier data is invalid
        """
        self.logger.info("Creating new supplier")

        # Validate required fields
        if 'name' not in supplier_data:
            self.logger.warning("Missing required field: name")
            raise ValidationError("Supplier name is required")

        # Set default values
        supplier_id = self._next_supplier_id
        self._next_supplier_id += 1

        # Create supplier
        supplier = {
            'id': supplier_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': SupplierStatus.ACTIVE.name,
            **supplier_data
        }

        self._suppliers[supplier_id] = supplier
        self._supplier_products[supplier_id] = []
        self._supplier_orders[supplier_id] = []

        self.logger.info(f"Created supplier with ID {supplier_id}")
        return supplier

    def update_supplier(self, supplier_id: int, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier.

        Args:
            supplier_id (int): ID of the supplier to update
            supplier_data (Dict[str, Any]): New supplier data

        Returns:
            Dict[str, Any]: Updated supplier data

        Raises:
            NotFoundError: If the supplier doesn't exist
            ValidationError: If the supplier data is invalid
        """
        self.logger.info(f"Updating supplier with ID {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Get current supplier
        supplier = self._suppliers[supplier_id]

        # Update fields
        for key, value in supplier_data.items():
            if key not in ['id', 'created_at']:
                supplier[key] = value

        # Update timestamp
        supplier['updated_at'] = datetime.now()

        self.logger.info(f"Updated supplier with ID {supplier_id}")
        return supplier

    def delete_supplier(self, supplier_id: int) -> bool:
        """Delete a supplier.

        Args:
            supplier_id (int): ID of the supplier to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        self.logger.info(f"Deleting supplier with ID {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Delete supplier
        del self._suppliers[supplier_id]

        # Delete related data
        self._supplier_products.pop(supplier_id, None)
        self._supplier_orders.pop(supplier_id, None)

        self.logger.info(f"Deleted supplier with ID {supplier_id}")
        return True

    def get_suppliers_by_status(self, status: SupplierStatus) -> List[Dict[str, Any]]:
        """Get suppliers by their status.

        Args:
            status (SupplierStatus): The status to filter by

        Returns:
            List[Dict[str, Any]]: List of supplier data dictionaries with the specified status
        """
        self.logger.info(f"Retrieving suppliers with status {status}")

        # Convert enum to string for comparison if needed
        status_str = status.name if hasattr(status, 'name') else str(status)

        return [
            supplier for supplier in self._suppliers.values()
            if supplier.get('status') == status_str
        ]

    def change_supplier_status(self, supplier_id: int, new_status: SupplierStatus) -> Dict[str, Any]:
        """Change a supplier's status.

        Args:
            supplier_id (int): ID of the supplier to update
            new_status (SupplierStatus): New status for the supplier

        Returns:
            Dict[str, Any]: Updated supplier data

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        self.logger.info(f"Changing supplier {supplier_id} status to {new_status}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Get current supplier
        supplier = self._suppliers[supplier_id]

        # Update status
        supplier['status'] = new_status.name if hasattr(new_status, 'name') else str(new_status)
        supplier['updated_at'] = datetime.now()

        self.logger.info(f"Changed supplier {supplier_id} status to {new_status}")
        return supplier

    def search_suppliers(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for suppliers by name, contact, or description.

        Args:
            search_term (str): The search term to filter by

        Returns:
            List[Dict[str, Any]]: List of matching supplier data dictionaries
        """
        self.logger.info(f"Searching suppliers with term '{search_term}'")

        search_term = search_term.lower()
        results = []

        for supplier in self._suppliers.values():
            if (
                search_term in supplier.get('name', '').lower() or
                search_term in supplier.get('contact', '').lower() or
                search_term in supplier.get('email', '').lower() or
                search_term in supplier.get('phone', '').lower() or
                search_term in supplier.get('description', '').lower()
            ):
                results.append(supplier)

        return results

    def get_supplier_products(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get all products provided by a supplier.

        Args:
            supplier_id (int): ID of the supplier to get products for

        Returns:
            List[Dict[str, Any]]: List of product data dictionaries

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        self.logger.info(f"Retrieving products for supplier {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Return products
        return self._supplier_products.get(supplier_id, [])

    def add_product_to_supplier(self, supplier_id: int, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a product to a supplier.

        Args:
            supplier_id (int): ID of the supplier to add the product to
            product_data (Dict[str, Any]): Product data to add

        Returns:
            Dict[str, Any]: Added product data

        Raises:
            NotFoundError: If the supplier doesn't exist
            ValidationError: If the product data is invalid
        """
        self.logger.info(f"Adding product to supplier {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Validate product data
        if 'name' not in product_data:
            self.logger.warning("Missing required field: name")
            raise ValidationError("Product name is required")

        # Create product
        product = {
            'id': len(self._supplier_products.get(supplier_id, [])) + 1,
            'supplier_id': supplier_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            **product_data
        }

        # Add product to supplier
        if supplier_id not in self._supplier_products:
            self._supplier_products[supplier_id] = []

        self._supplier_products[supplier_id].append(product)

        # Update supplier
        self._suppliers[supplier_id]['updated_at'] = datetime.now()

        self.logger.info(f"Added product {product['id']} to supplier {supplier_id}")
        return product

    def get_supplier_orders(self, supplier_id: int) -> List[Dict[str, Any]]:
        """Get all orders placed with a supplier.

        Args:
            supplier_id (int): ID of the supplier to get orders for

        Returns:
            List[Dict[str, Any]]: List of order data dictionaries

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        self.logger.info(f"Retrieving orders for supplier {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Return orders
        return self._supplier_orders.get(supplier_id, [])

    def add_order_to_supplier(self, supplier_id: int, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add an order to a supplier.

        Args:
            supplier_id (int): ID of the supplier to add the order to
            order_data (Dict[str, Any]): Order data to add

        Returns:
            Dict[str, Any]: Added order data

        Raises:
            NotFoundError: If the supplier doesn't exist
            ValidationError: If the order data is invalid
        """
        self.logger.info(f"Adding order to supplier {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Validate order data
        if 'items' not in order_data or not order_data['items']:
            self.logger.warning("Missing required field: items")
            raise ValidationError("Order must have at least one item")

        # Create order
        order = {
            'id': len(self._supplier_orders.get(supplier_id, [])) + 1,
            'supplier_id': supplier_id,
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'status': 'new',
            **order_data
        }

        # Add order to supplier
        if supplier_id not in self._supplier_orders:
            self._supplier_orders[supplier_id] = []

        self._supplier_orders[supplier_id].append(order)

        # Update supplier
        self._suppliers[supplier_id]['updated_at'] = datetime.now()

        self.logger.info(f"Added order {order['id']} to supplier {supplier_id}")
        return order

    # IBaseService implementation methods

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier.

        Args:
            data (Dict[str, Any]): Data for creating the supplier

        Returns:
            Dict[str, Any]: Created supplier

        Raises:
            ValidationError: If data is invalid
        """
        return self.create_supplier(data)

    def get_by_id(self, entity_id: Any) -> Optional[Dict[str, Any]]:
        """Retrieve a supplier by its identifier.

        Args:
            entity_id (Any): Unique identifier for the supplier

        Returns:
            Optional[Dict[str, Any]]: Retrieved supplier or None if not found
        """
        try:
            return self.get_supplier_by_id(int(entity_id))
        except NotFoundError:
            return None

    def update(self, entity_id: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing supplier.

        Args:
            entity_id (Any): Unique identifier for the supplier
            data (Dict[str, Any]): Updated data for the supplier

        Returns:
            Dict[str, Any]: Updated supplier

        Raises:
            NotFoundError: If supplier doesn't exist
            ValidationError: If update data is invalid
        """
        return self.update_supplier(int(entity_id), data)

    def delete(self, entity_id: Any) -> bool:
        """Delete a supplier by its identifier.

        Args:
            entity_id (Any): Unique identifier for the supplier

        Returns:
            bool: True if deletion was successful, False otherwise

        Raises:
            NotFoundError: If supplier doesn't exist
        """
        return self.delete_supplier(int(entity_id))

    def list_suppliers(self) -> List[Dict[str, Any]]:
        """List all suppliers.

        Returns:
            List[Dict[str, Any]]: List of all suppliers
        """
        return self.get_all_suppliers()

    def get_supplier(self, supplier_id: int) -> Dict[str, Any]:
        """Get a supplier by its ID.

        Args:
            supplier_id (int): The ID of the supplier to retrieve

        Returns:
            Dict[str, Any]: The supplier data

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        return self.get_supplier_by_id(supplier_id)

    def evaluate_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Evaluate the performance of a supplier.

        Args:
            supplier_id (int): The ID of the supplier to evaluate

        Returns:
            Dict[str, Any]: Supplier performance metrics

        Raises:
            NotFoundError: If the supplier doesn't exist
        """
        self.logger.info(f"Evaluating performance of supplier {supplier_id}")

        # Check if supplier exists
        if supplier_id not in self._suppliers:
            self.logger.warning(f"Supplier with ID {supplier_id} not found")
            raise NotFoundError(f"Supplier with ID {supplier_id} not found")

        # Get supplier
        supplier = self._suppliers[supplier_id]

        # Get orders
        orders = self._supplier_orders.get(supplier_id, [])
        total_orders = len(orders)

        if total_orders == 0:
            return {
                'supplier_id': supplier_id,
                'supplier_name': supplier.get('name', ''),
                'total_orders': 0,
                'rating': supplier.get('rating', 0),
                'on_time_delivery_rate': 0,
                'quality_rating': 0,
                'response_time': 0,
                'performance_score': 0
            }

        # Calculate performance metrics
        on_time_orders = sum(1 for order in orders if order.get('delivered_on_time', False))
        on_time_delivery_rate = (on_time_orders / total_orders) * 100 if total_orders > 0 else 0

        # Average quality rating (1-5)
        quality_ratings = [order.get('quality_rating', 0) for order in orders if 'quality_rating' in order]
        quality_rating = sum(quality_ratings) / len(quality_ratings) if quality_ratings else 0

        # Average response time in hours
        response_times = [order.get('response_time', 0) for order in orders if 'response_time' in order]
        response_time = sum(response_times) / len(response_times) if response_times else 0

        # Overall performance score (weighted average)
        weights = {
            'on_time_delivery': 0.4,
            'quality': 0.4,
            'response_time': 0.2
        }

        # Normalize response time (lower is better) - assume 24 hours is the baseline
        normalized_response_time = max(0, 100 - (response_time / 24 * 100))

        performance_score = (
            weights['on_time_delivery'] * on_time_delivery_rate +
            weights['quality'] * (quality_rating / 5 * 100) +
            weights['response_time'] * normalized_response_time
        )

        return {
            'supplier_id': supplier_id,
            'supplier_name': supplier.get('name', ''),
            'total_orders': total_orders,
            'rating': supplier.get('rating', 0),
            'on_time_delivery_rate': round(on_time_delivery_rate, 2),
            'quality_rating': round(quality_rating, 2),
            'response_time': round(response_time, 2),
            'performance_score': round(performance_score, 2)
        }
