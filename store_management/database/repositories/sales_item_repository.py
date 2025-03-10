# database/repositories/sales_item_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime
from sqlalchemy import func, or_, and_, desc

from database.models.sales_item import SalesItem
from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError


class SalesItemRepository(BaseRepository[SalesItem]):
    """Repository for sales item operations.

    This repository provides methods for querying and manipulating sales item data,
    including relationships with sales orders and products.
    """

    def _get_model_class(self) -> Type[SalesItem]:
        """Return the model class this repository manages.

        Returns:
            The SalesItem model class
        """
        return SalesItem

    # Sales item-specific query methods

    def get_by_sales(self, sales_id: int) -> List[SalesItem]:
        """Get sales items for a specific sales order.

        Args:
            sales_id: ID of the sales order

        Returns:
            List of sales item instances for the specified sales order
        """
        self.logger.debug(f"Getting sales items for sales order {sales_id}")
        return self.session.query(SalesItem).filter(SalesItem.sales_id == sales_id).all()

    def get_by_product(self, product_id: int) -> List[SalesItem]:
        """Get sales items for a specific product.

        Args:
            product_id: ID of the product

        Returns:
            List of sales item instances for the specified product
        """
        self.logger.debug(f"Getting sales items for product {product_id}")
        return self.session.query(SalesItem).filter(SalesItem.product_id == product_id).all()

    def get_items_with_details(self, sales_id: int) -> List[Dict[str, Any]]:
        """Get sales items with product details.

        Args:
            sales_id: ID of the sales order

        Returns:
            List of sales items with product details
        """
        self.logger.debug(f"Getting sales items with details for sales order {sales_id}")
        from database.models.product import Product

        items = self.session.query(SalesItem, Product).join(
            Product,
            Product.id == SalesItem.product_id
        ).filter(
            SalesItem.sales_id == sales_id
        ).all()

        result = []
        for item, product in items:
            item_dict = item.to_dict()
            item_dict['product_name'] = product.name
            item_dict['product_description'] = product.description
            item_dict['subtotal'] = item.quantity * item.price

            result.append(item_dict)

        return result

    # Business logic methods

    def calculate_total_amount(self, sales_id: int) -> float:
        """Calculate the total amount for a sales order.

        Args:
            sales_id: ID of the sales order

        Returns:
            Total amount for the sales order
        """
        self.logger.debug(f"Calculating total amount for sales order {sales_id}")

        result = self.session.query(
            func.sum(SalesItem.quantity * SalesItem.price).label('total')
        ).filter(
            SalesItem.sales_id == sales_id
        ).scalar()

        return float(result) if result is not None else 0.0

    def update_quantity(self, sales_item_id: int, new_quantity: int) -> Dict[str, Any]:
        """Update the quantity of a sales item.

        Args:
            sales_item_id: ID of the sales item
            new_quantity: New quantity value

        Returns:
            Updated sales item data

        Raises:
            EntityNotFoundError: If sales item not found
            ValidationError: If new quantity is invalid
        """
        self.logger.debug(f"Updating quantity for sales item {sales_item_id} to {new_quantity}")

        sales_item = self.get_by_id(sales_item_id)
        if not sales_item:
            raise EntityNotFoundError(f"Sales item with ID {sales_item_id} not found")

        if new_quantity <= 0:
            raise ValidationError("Quantity must be greater than zero")

        try:
            # Update quantity
            sales_item.quantity = new_quantity

            # Update sales item
            self.update(sales_item)

            # Calculate new subtotal
            subtotal = sales_item.quantity * sales_item.price

            # Update total on the parent sales order
            from database.models.sales import Sales
            sales = self.session.query(Sales).get(sales_item.sales_id)
            if sales:
                # Recalculate total from all items
                total = self.calculate_total_amount(sales_item.sales_id)
                sales.total_amount = total
                self.session.add(sales)
                self.session.flush()

            # Prepare result
            result = sales_item.to_dict()
            result['subtotal'] = subtotal

            return result

        except Exception as e:
            self.logger.error(f"Error updating sales item quantity: {str(e)}")
            raise ValidationError(f"Failed to update sales item quantity: {str(e)}")

    # GUI-specific functionality

    def get_top_selling_products(self, period_days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top selling products for a specific period.

        Args:
            period_days: Number of days to look back
            limit: Maximum number of products to return

        Returns:
            List of top selling products with quantities and revenue
        """
        self.logger.debug(f"Getting top selling products for the last {period_days} days")
        from database.models.product import Product
        from database.models.sales import Sales

        # Calculate start date
        start_date = datetime.now() - timedelta(days=period_days)

        # Query for top products
        top_products = self.session.query(
            Product.id,
            Product.name,
            func.sum(SalesItem.quantity).label('total_quantity'),
            func.sum(SalesItem.quantity * SalesItem.price).label('total_revenue')
        ).join(
            SalesItem,
            SalesItem.product_id == Product.id
        ).join(
            Sales,
            Sales.id == SalesItem.sales_id
        ).filter(
            Sales.created_at >= start_date
        ).group_by(
            Product.id,
            Product.name
        ).order_by(
            func.sum(SalesItem.quantity * SalesItem.price).desc()
        ).limit(limit).all()

        # Format result
        result = []
        for id, name, total_quantity, total_revenue in top_products:
            result.append({
                'product_id': id,
                'product_name': name,
                'total_quantity': total_quantity,
                'total_revenue': float(total_revenue)
            })

        return result