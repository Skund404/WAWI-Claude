# database/repositories/product_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc, case

from database.models.product import Product
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import ProjectType, InventoryStatus


class ProductRepository(BaseRepository[Product]):
    """Repository for product management operations.

    This repository provides methods for managing product data, including
    pattern associations, pricing, and inventory integration.
    """

    def _get_model_class(self) -> Type[Product]:
        """Return the model class this repository manages.

        Returns:
            The Product model class
        """
        return Product

    # Basic query methods

    def get_by_name(self, name: str) -> Optional[Product]:
        """Get product by exact name match.

        Args:
            name: Product name to search for

        Returns:
            Product instance or None if not found
        """
        self.logger.debug(f"Getting product with name '{name}'")
        return self.session.query(Product).filter(Product.name == name).first()

    def get_by_type(self, product_type: ProjectType) -> List[Product]:
        """Get products by type.

        Args:
            product_type: Product type to filter by

        Returns:
            List of product instances with the specified type
        """
        self.logger.debug(f"Getting products with type '{product_type.value}'")
        type_field = 'type' if hasattr(Product, 'type') else 'product_type'
        if hasattr(Product, type_field):
            return self.session.query(Product).filter(getattr(Product, type_field) == product_type).all()
        else:
            # If no type field, return empty list
            return []

    def search_products(self, search_term: str) -> List[Product]:
        """Search products by term in name and description.

        Args:
            search_term: Term to search for

        Returns:
            List of matching product instances
        """
        self.logger.debug(f"Searching products for '{search_term}'")
        search_fields = ['name']
        if hasattr(Product, 'description'):
            search_fields.append('description')

        return self.search(search_term, search_fields)

    def get_in_stock_products(self) -> List[Dict[str, Any]]:
        """Get products that are currently in stock.

        Returns:
            List of product dictionaries with inventory information
        """
        self.logger.debug("Getting in-stock products")
        from database.models.inventory import Inventory

        # Join with inventory to get stock information
        query = self.session.query(Product, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Product.id) &
                 (Inventory.item_type == 'product')). \
            filter(Inventory.quantity > 0)

        # Format results
        result = []
        for product, inventory in query.all():
            product_dict = product.to_dict()
            product_dict['current_stock'] = inventory.quantity
            product_dict['stock_status'] = inventory.status.value
            product_dict['storage_location'] = inventory.storage_location
            result.append(product_dict)

        return result

    # Pattern and pricing methods

    def get_product_with_patterns(self, product_id: int) -> Dict[str, Any]:
        """Get product with all associated patterns.

        Args:
            product_id: ID of the product

        Returns:
            Product dictionary with pattern information

        Raises:
            EntityNotFoundError: If product not found
        """
        self.logger.debug(f"Getting product {product_id} with patterns")
        from database.models.pattern import Pattern
        from database.models.relationship_tables import product_pattern_table

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        # Get product data
        result = product.to_dict()

        # Get associated patterns
        patterns = self.session.query(Pattern). \
            join(product_pattern_table). \
            filter(product_pattern_table.c.product_id == product_id).all()

        result['patterns'] = [pattern.to_dict() for pattern in patterns]

        return result

    def associate_pattern(self, product_id: int, pattern_id: int) -> Dict[str, Any]:
        """Associate a pattern with a product.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern to associate

        Returns:
            Updated product with patterns

        Raises:
            EntityNotFoundError: If product or pattern not found
        """
        self.logger.debug(f"Associating pattern {pattern_id} with product {product_id}")
        from database.models.pattern import Pattern

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        pattern = self.session.query(Pattern).get(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        try:
            # Check if association already exists
            if pattern in product.patterns:
                return self.get_product_with_patterns(product_id)

            # Add association
            product.patterns.append(pattern)
            self.session.flush()

            return self.get_product_with_patterns(product_id)
        except Exception as e:
            self.logger.error(f"Error associating pattern with product: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to associate pattern with product: {str(e)}")

    def disassociate_pattern(self, product_id: int, pattern_id: int) -> Dict[str, Any]:
        """Remove association between a product and a pattern.

        Args:
            product_id: ID of the product
            pattern_id: ID of the pattern to disassociate

        Returns:
            Updated product with patterns

        Raises:
            EntityNotFoundError: If product or pattern not found
            ValidationError: If pattern is not associated with product
        """
        self.logger.debug(f"Disassociating pattern {pattern_id} from product {product_id}")
        from database.models.pattern import Pattern

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        pattern = self.session.query(Pattern).get(pattern_id)
        if not pattern:
            raise EntityNotFoundError(f"Pattern with ID {pattern_id} not found")

        try:
            # Check if association exists
            if pattern not in product.patterns:
                raise ValidationError(f"Pattern {pattern_id} is not associated with product {product_id}")

            # Remove association
            product.patterns.remove(pattern)
            self.session.flush()

            return self.get_product_with_patterns(product_id)
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error disassociating pattern from product: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to disassociate pattern from product: {str(e)}")

    def update_product_price(self, product_id: int,
                             price: float,
                             recalculate_sales: bool = False) -> Dict[str, Any]:
        """Update product price.

        Args:
            product_id: ID of the product
            price: New price
            recalculate_sales: Whether to update prices in open sales orders

        Returns:
            Updated product data

        Raises:
            EntityNotFoundError: If product not found
            ValidationError: If price is invalid
        """
        self.logger.debug(f"Updating price for product {product_id} to {price}")

        if price < 0:
            raise ValidationError("Price cannot be negative")

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        try:
            # Update product price
            product.price = price
            self.update(product)

            # Recalculate open sales if requested
            if recalculate_sales:
                self._update_open_sales_prices(product_id, price)

            return product.to_dict()
        except Exception as e:
            self.logger.error(f"Error updating product price: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to update product price: {str(e)}")

    def _update_open_sales_prices(self, product_id: int, new_price: float) -> int:
        """Update prices in open sales orders for a product.

        Args:
            product_id: ID of the product
            new_price: New price

        Returns:
            Number of updated sales items
        """
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem

        # Define open sales statuses (those where price changes are allowed)
        open_statuses = ['QUOTE_REQUEST', 'DESIGN_CONSULTATION', 'DEPOSIT_RECEIVED']

        # Find sales items for this product in open sales
        updated_items = self.session.query(SalesItem). \
            join(Sales, SalesItem.sales_id == Sales.id). \
            filter(SalesItem.product_id == product_id). \
            filter(Sales.status.in_(open_statuses)). \
            all()

        # Update each item
        for item in updated_items:
            old_price = item.price
            old_total = old_price * item.quantity

            # Update price
            item.price = new_price

            # Adjust sale total amount
            sales = self.session.query(Sales).get(item.sales_id)
            if sales:
                new_total = new_price * item.quantity
                price_diff = new_total - old_total
                sales.total_amount += price_diff
                self.session.add(sales)

        self.session.flush()
        return len(updated_items)

    # Inventory integration methods

    def create_product_with_inventory(self, product_data: Dict[str, Any],
                                      inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product with associated inventory record.

        Args:
            product_data: Product data dictionary
            inventory_data: Inventory data dictionary

        Returns:
            Created product with inventory information

        Raises:
            ValidationError: If validation fails
        """
        self.logger.debug("Creating new product with inventory")
        from database.models.inventory import Inventory

        try:
            # Create product
            product = Product(**product_data)
            created_product = self.create(product)

            # Create inventory record
            inventory = Inventory(
                item_id=created_product.id,
                item_type='product',
                **inventory_data
            )
            self.session.add(inventory)
            self.session.flush()

            # Prepare result
            result = created_product.to_dict()
            result['inventory'] = inventory.to_dict()

            return result
        except Exception as e:
            self.logger.error(f"Error creating product with inventory: {str(e)}")
            self.session.rollback()
            raise ValidationError(f"Failed to create product with inventory: {str(e)}")

    def update_product_stock(self, product_id: int,
                             quantity: float,
                             update_type: str = 'set',
                             location: Optional[str] = None) -> Dict[str, Any]:
        """Update product inventory.

        Args:
            product_id: ID of the product
            quantity: New quantity or adjustment amount
            update_type: Type of update ('set', 'add', 'subtract')
            location: Optional storage location

        Returns:
            Updated product with inventory information

        Raises:
            EntityNotFoundError: If product not found
            ValidationError: If update would result in negative inventory
        """
        self.logger.debug(f"Updating stock for product {product_id}, {update_type} {quantity}")
        from database.models.inventory import Inventory

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        try:
            # Find or create inventory record
            inventory = self.session.query(Inventory). \
                filter(Inventory.item_id == product_id). \
                filter(Inventory.item_type == 'product').first()

            if not inventory:
                # Create new inventory record
                inventory = Inventory(
                    item_id=product_id,
                    item_type='product',
                    quantity=0,
                    status=InventoryStatus.OUT_OF_STOCK,
                    storage_location=location or ''
                )
                self.session.add(inventory)

            # Update quantity based on update type
            old_quantity = inventory.quantity

            if update_type == 'set':
                inventory.quantity = quantity
            elif update_type == 'add':
                inventory.quantity += quantity
            elif update_type == 'subtract':
                if inventory.quantity < quantity:
                    raise ValidationError(f"Cannot subtract {quantity} from current stock {inventory.quantity}")
                inventory.quantity -= quantity
            else:
                raise ValidationError(f"Invalid update type: {update_type}")

            # Update status based on new quantity
            if inventory.quantity <= 0:
                inventory.status = InventoryStatus.OUT_OF_STOCK
            elif hasattr(product, 'min_stock') and inventory.quantity <= product.min_stock:
                inventory.status = InventoryStatus.LOW_STOCK
            else:
                inventory.status = InventoryStatus.IN_STOCK

            # Update location if provided
            if location:
                inventory.storage_location = location

            # Save changes
            self.session.flush()

            # Prepare result
            result = product.to_dict()
            result['inventory'] = inventory.to_dict()
            result['inventory']['previous_quantity'] = old_quantity

            return result
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating product stock: {str(e)}")
            self.session.rollback()
            raise RepositoryError(f"Failed to update product stock: {str(e)}")

    # Sales and analytics methods

    def get_sales_history(self, product_id: int,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get sales history for a product.

        Args:
            product_id: ID of the product
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            List of sales records for the product

        Raises:
            EntityNotFoundError: If product not found
        """
        self.logger.debug(f"Getting sales history for product {product_id}")
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        # Build query for sales items with this product
        query = self.session.query(SalesItem, Sales). \
            join(Sales, SalesItem.sales_id == Sales.id). \
            filter(SalesItem.product_id == product_id)

        # Apply date filters if provided
        if start_date:
            query = query.filter(Sales.created_at >= start_date)
        if end_date:
            query = query.filter(Sales.created_at <= end_date)

        # Order by date
        query = query.order_by(Sales.created_at.desc())

        # Format results
        results = []
        for item, sale in query.all():
            results.append({
                'sales_id': sale.id,
                'sales_item_id': item.id,
                'date': sale.created_at.isoformat() if hasattr(sale, 'created_at') else None,
                'quantity': item.quantity,
                'price': item.price,
                'total': item.price * item.quantity,
                'sales_status': sale.status.value if hasattr(sale, 'status') else None,
                'payment_status': sale.payment_status.value if hasattr(sale, 'payment_status') else None
            })

        return results

    def calculate_sales_metrics(self, product_id: int) -> Dict[str, Any]:
        """Calculate sales metrics for a product.

        Args:
            product_id: ID of the product

        Returns:
            Dictionary with sales metrics

        Raises:
            EntityNotFoundError: If product not found
        """
        self.logger.debug(f"Calculating sales metrics for product {product_id}")
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem

        product = self.get_by_id(product_id)
        if not product:
            raise EntityNotFoundError(f"Product with ID {product_id} not found")

        # Only include completed sales
        completed_statuses = ['COMPLETED', 'DELIVERED']

        # Calculate metrics
        metrics_query = self.session.query(
            func.count(SalesItem.id).label('order_count'),
            func.sum(SalesItem.quantity).label('units_sold'),
            func.sum(SalesItem.quantity * SalesItem.price).label('total_revenue'),
            func.avg(SalesItem.price).label('average_price')
        ).join(
            Sales, SalesItem.sales_id == Sales.id
        ).filter(
            SalesItem.product_id == product_id,
            Sales.status.in_(completed_statuses)
        )

        metrics = metrics_query.first()

        # Calculate sales velocity (sales per month)
        # First sale date
        first_sale_date = self.session.query(func.min(Sales.created_at)). \
            join(SalesItem, Sales.id == SalesItem.sales_id). \
            filter(SalesItem.product_id == product_id).scalar()

        # Last sale date
        last_sale_date = self.session.query(func.max(Sales.created_at)). \
            join(SalesItem, Sales.id == SalesItem.sales_id). \
            filter(SalesItem.product_id == product_id).scalar()

        # Calculate velocity
        units_sold = metrics.units_sold or 0
        velocity = 0

        if first_sale_date and last_sale_date and first_sale_date != last_sale_date:
            # Calculate months between dates
            days_between = (last_sale_date - first_sale_date).days
            months_between = max(1, days_between / 30)  # At least 1 month to avoid division by zero

            velocity = units_sold / months_between
        elif units_sold > 0:
            # Only one sale date, use 1 month
            velocity = units_sold

        # Format results
        return {
            'product_id': product_id,
            'product_name': product.name,
            'order_count': metrics.order_count or 0,
            'units_sold': units_sold,
            'total_revenue': float(metrics.total_revenue) if metrics.total_revenue else 0,
            'average_price': float(metrics.average_price) if metrics.average_price else 0,
            'first_sale_date': first_sale_date.isoformat() if first_sale_date else None,
            'last_sale_date': last_sale_date.isoformat() if last_sale_date else None,
            'sales_velocity': velocity  # Units per month
        }

    # GUI-specific functionality

    def get_product_dashboard_data(self) -> Dict[str, Any]:
        """Get data for product dashboard in GUI.

        Returns:
            Dictionary with dashboard data
        """
        self.logger.debug("Getting product dashboard data")
        from database.models.inventory import Inventory

        # Count by type (if applicable)
        type_counts = {}
        if hasattr(Product, 'type'):
            type_query = self.session.query(
                Product.type,
                func.count().label('count')
            ).group_by(Product.type).all()

            type_counts = {type_.value: count for type_, count in type_query}

        # Get inventory status counts
        inventory_query = self.session.query(
            Inventory.status,
            func.count().label('count')
        ).filter(
            Inventory.item_type == 'product'
        ).group_by(Inventory.status).all()

        inventory_status = {status.value: count for status, count in inventory_query}

        # Get low stock products
        low_stock_query = self.session.query(Product, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Product.id) &
                 (Inventory.item_type == 'product')). \
            filter(Inventory.status == InventoryStatus.LOW_STOCK)

        low_stock = []
        for product, inventory in low_stock_query.all():
            product_dict = product.to_dict()
            product_dict['current_stock'] = inventory.quantity
            product_dict['min_stock'] = product.min_stock if hasattr(product, 'min_stock') else None
            product_dict['storage_location'] = inventory.storage_location
            low_stock.append(product_dict)

        # Get out of stock products
        out_of_stock_query = self.session.query(Product, Inventory). \
            join(Inventory,
                 (Inventory.item_id == Product.id) &
                 (Inventory.item_type == 'product')). \
            filter(Inventory.status == InventoryStatus.OUT_OF_STOCK)

        out_of_stock = []
        for product, inventory in out_of_stock_query.all():
            product_dict = product.to_dict()
            product_dict['current_stock'] = inventory.quantity
            product_dict['min_stock'] = product.min_stock if hasattr(product, 'min_stock') else None
            product_dict['storage_location'] = inventory.storage_location
            out_of_stock.append(product_dict)

        # Get top selling products
        from database.models.sales import Sales
        from database.models.sales_item import SalesItem

        top_products_query = self.session.query(
            Product.id,
            Product.name,
            func.sum(SalesItem.quantity).label('units_sold')
        ).join(
            SalesItem, SalesItem.product_id == Product.id
        ).join(
            Sales, Sales.id == SalesItem.sales_id
        ).group_by(
            Product.id, Product.name
        ).order_by(
            func.sum(SalesItem.quantity).desc()
        ).limit(5)

        top_products = [{
            'id': product_id,
            'name': name,
            'units_sold': units_sold
        } for product_id, name, units_sold in top_products_query.all()]

        # Combine all data
        return {
            'total_products': self.count(),
            'type_counts': type_counts,
            'inventory_status': inventory_status,
            'low_stock_count': len(low_stock),
            'low_stock_products': low_stock[:5],  # Top 5
            'out_of_stock_count': len(out_of_stock),
            'out_of_stock_products': out_of_stock[:5],  # Top 5
            'top_selling_products': top_products
        }

    def filter_products_for_gui(self,
                                search_term: Optional[str] = None,
                                product_types: Optional[List[str]] = None,
                                in_stock_only: bool = False,
                                pattern_id: Optional[int] = None,
                                min_price: Optional[float] = None,
                                max_price: Optional[float] = None,
                                sort_by: str = 'name',
                                sort_dir: str = 'asc',
                                page: int = 1,
                                page_size: int = 20) -> Dict[str, Any]:
        """Filter and paginate products for GUI display.

        Args:
            search_term: Optional search term
            product_types: Optional list of product types to filter by
            in_stock_only: Whether to show only in-stock products
            pattern_id: Optional pattern ID to filter by associated pattern
            min_price: Optional minimum price
            max_price: Optional maximum price
            sort_by: Field to sort by
            sort_dir: Sort direction ('asc' or 'desc')
            page: Page number
            page_size: Page size

        Returns:
            Dict with paginated results and metadata
        """
        self.logger.debug(f"Filtering products for GUI: search='{search_term}', types={product_types}")
        from database.models.inventory import Inventory
        from database.models.pattern import Pattern
        from database.models.relationship_tables import product_pattern_table

        # Start with base query
        query = self.session.query(Product)

        # Apply search filter if provided
        if search_term:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%") if hasattr(Product, 'description') else False
                )
            )

        # Apply type filter if applicable
        if product_types and hasattr(Product, 'type'):
            query = query.filter(Product.type.in_(product_types))

        # Apply price filters
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)

        # Apply pattern filter
        if pattern_id is not None:
            query = query.join(
                product_pattern_table,
                product_pattern_table.c.product_id == Product.id
            ).filter(product_pattern_table.c.pattern_id == pattern_id)

        # Apply stock filter
        if in_stock_only:
            query = query.join(
                Inventory,
                (Inventory.item_id == Product.id) & (Inventory.item_type == 'product')
            ).filter(Inventory.quantity > 0)

        # Get total count for pagination
        total_count = query.count()

        # Apply sorting
        if sort_by == 'name':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Product.name.desc())
            else:
                query = query.order_by(Product.name.asc())
        elif sort_by == 'price':
            if sort_dir.lower() == 'desc':
                query = query.order_by(Product.price.desc())
            else:
                query = query.order_by(Product.price.asc())
        elif sort_by == 'type' and hasattr(Product, 'type'):
            if sort_dir.lower() == 'desc':
                query = query.order_by(Product.type.desc())
            else:
                query = query.order_by(Product.type.asc())
        elif sort_by == 'created_at' and hasattr(Product, 'created_at'):
            if sort_dir.lower() == 'desc':
                query = query.order_by(Product.created_at.desc())
            else:
                query = query.order_by(Product.created_at.asc())
        else:
            # Default to name
            query = query.order_by(Product.name.asc())

        # Apply pagination
        query = query.offset((page - 1) * page_size).limit(page_size)

        # Execute query
        products = query.all()

        # Get inventory data for products
        product_ids = [p.id for p in products]
        inventories = {}

        if product_ids:
            inventory_query = self.session.query(Inventory). \
                filter(Inventory.item_id.in_(product_ids)). \
                filter(Inventory.item_type == 'product')

            inventories = {inv.item_id: inv for inv in inventory_query.all()}

        # Format results
        items = []
        for product in products:
            product_dict = product.to_dict()

            # Add inventory data if available
            if product.id in inventories:
                inventory = inventories[product.id]
                product_dict['current_stock'] = inventory.quantity
                product_dict['stock_status'] = inventory.status.value
                product_dict['storage_location'] = inventory.storage_location
            else:
                product_dict['current_stock'] = 0
                product_dict['stock_status'] = 'NOT_TRACKED'
                product_dict['storage_location'] = None

            items.append(product_dict)

        # Return paginated results with metadata
        return {
            'items': items,
            'total': total_count,
            'page': page,
            'page_size': page_size,
            'pages': (total_count + page_size - 1) // page_size,
            'has_next': page < ((total_count + page_size - 1) // page_size),
            'has_prev': page > 1
        }

    def export_product_data(self, format: str = "csv") -> Dict[str, Any]:
        """Export product data to specified format.

        Args:
            format: Export format ("csv" or "json")

        Returns:
            Dict with export data and metadata
        """
        self.logger.debug(f"Exporting product data in {format} format")
        from database.models.inventory import Inventory

        # Get all products
        products = self.get_all(limit=10000)  # Reasonable limit

        # Get inventory data
        product_ids = [p.id for p in products]
        inventories = {}

        if product_ids:
            inventory_query = self.session.query(Inventory). \
                filter(Inventory.item_id.in_(product_ids)). \
                filter(Inventory.item_type == 'product')

            inventories = {inv.item_id: inv for inv in inventory_query.all()}

        # Format data
        data = []
        for product in products:
            product_dict = product.to_dict()

            # Add inventory data if available
            if product.id in inventories:
                inventory = inventories[product.id]
                product_dict['current_stock'] = inventory.quantity
                product_dict['stock_status'] = inventory.status.value
                product_dict['storage_location'] = inventory.storage_location
            else:
                product_dict['current_stock'] = 0
                product_dict['stock_status'] = 'NOT_TRACKED'
                product_dict['storage_location'] = None

            data.append(product_dict)

        # Create metadata
        metadata = {
            'count': len(data),
            'timestamp': datetime.now().isoformat(),
            'format': format,
            'total_inventory': sum(p['current_stock'] for p in data),
            'total_value': sum(p['current_stock'] * p['price'] for p in data)
        }

        return {
            'data': data,
            'metadata': metadata
        }