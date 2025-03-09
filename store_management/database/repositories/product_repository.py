# database/repositories/product_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from database.models.product import Product
from database.models.enums import MaterialType
from database.repositories.base_repository import BaseRepository

import logging
from typing import List, Optional, Dict, Any, Union


class ProductRepository(BaseRepository):
    """
    Repository for managing Product database operations.

    Provides methods for:
    - CRUD operations on Product entities
    - Advanced querying capabilities
    - Error handling and logging
    """

    def __init__(self, session: Session):
        """
        Initialize the Product Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Product)
        self.logger = logging.getLogger(self.__class__.__name__)

    def get_by_sku(self, sku: str) -> Optional[Product]:
        """
        Retrieve a product by its SKU.

        Args:
            sku (str): Unique Stock Keeping Unit identifier

        Returns:
            Optional[Product]: Product instance if found, None otherwise
        """
        try:
            product = self.session.execute(select(Product).filter_by(sku=sku)).scalar_one_or_none()
            return product
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving product by SKU: {str(e)}", extra={
                "sku": sku,
                "error": str(e)
            })
            return None

    def search_products(self,
                        search_term: Optional[str] = None,
                        material_type: Optional[MaterialType] = None,
                        min_price: Optional[float] = None,
                        max_price: Optional[float] = None,
                        is_active: Optional[bool] = None) -> List[Product]:
        """
        Advanced search for products with multiple filtering options.

        Args:
            search_term (Optional[str]): Search across name and description
            material_type (Optional[MaterialType]): Filter by material type
            min_price (Optional[float]): Minimum sale price
            max_price (Optional[float]): Maximum sale price
            is_active (Optional[bool]): Filter by active status

        Returns:
            List[Product]: List of products matching the search criteria
        """
        try:
            query = select(Product)

            # Name/description search
            if search_term:
                search_filter = or_(
                    Product.name.ilike(f"%{search_term}%"),
                    Product.description.ilike(f"%{search_term}%")
                )
                query = query.filter(search_filter)

            # Material type filter
            if material_type:
                query = query.filter(Product.material_type == material_type)

            # Price range filter
            if min_price is not None:
                query = query.filter(Product.sale_price >= min_price)

            if max_price is not None:
                query = query.filter(Product.sale_price <= max_price)

            # Active status filter
            if is_active is not None:
                query = query.filter(Product.is_active == is_active)

            # Execute query and log results
            results = query.all()

            self.logger.info("Product search completed", extra={
                "search_term": search_term,
                "material_type": material_type,
                "min_price": min_price,
                "max_price": max_price,
                "is_active": is_active,
                "results_count": len(results)
            })

            return results

        except SQLAlchemyError as e:
            self.logger.error(f"Error searching products: {str(e)}", extra={
                "search_params": {
                    "search_term": search_term,
                    "material_type": material_type,
                    "min_price": min_price,
                    "max_price": max_price,
                    "is_active": is_active
                },
                "error": str(e)
            })
            return []

    def calculate_inventory_value(self) -> Dict[str, Union[float, int]]:
        """
        Calculate total inventory value and related metrics.

        Returns:
            Dict containing inventory valuation metrics
        """
        try:
            # Get all active products
            active_products = self.search_products(is_active=True)

            # Calculate metrics
            total_inventory_value = sum(p.sale_price * 1 for p in active_products)
            total_product_count = len(active_products)

            # Group by material type
            material_type_breakdown = {}
            for material_type in MaterialType:
                material_products = [p for p in active_products if p.material_type == material_type]
                material_type_breakdown[material_type.name] = {
                    'count': len(material_products),
                    'total_value': sum(p.sale_price * 1 for p in material_products)
                }

            # Log inventory valuation
            self.logger.info("Inventory valuation calculated", extra={
                "total_value": total_inventory_value,
                "total_products": total_product_count,
                "material_type_breakdown": {k: v['count'] for k, v in material_type_breakdown.items()}
            })

            return {
                'total_inventory_value': total_inventory_value,
                'total_product_count': total_product_count,
                'material_type_breakdown': material_type_breakdown
            }

        except Exception as e:
            self.logger.error(f"Error calculating inventory value: {str(e)}", extra={
                "error": str(e)
            })
            return {
                'total_inventory_value': 0,
                'total_product_count': 0,
                'material_type_breakdown': {}
            }