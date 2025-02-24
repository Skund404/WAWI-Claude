from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/repositories/product_repository.py

Product repository for database access.
"""
logger = logging.getLogger(__name__)


class ProductRepository(BaseRepository):
    """
    Repository for Product model database access.

    This class provides specialized operations for the Product model.
    """

    @inject(MaterialService)
        def __init__(self, session: Session):
        """
        Initialize a new ProductRepository instance.

        Args:
            session: SQLAlchemy session.
        """
        super().__init__(session, Product)

        @inject(MaterialService)
            def get_by_id(self, product_id: int) -> Optional[Product]:
        """
        Get a product by ID.

        Args:
            product_id: The ID of the product.

        Returns:
            The product, or None if not found.
        """
        try:
            return self.session.query(Product).get(product_id)
        except SQLAlchemyError as e:
            logger.error(
                f'Error retrieving product with ID {product_id}: {str(e)}')
            return None

        @inject(MaterialService)
            def get_all(self, limit: Optional[int] = None, offset: Optional[int] = None
                    ) -> List[Product]:
        """
        Get all products.

        Args:
            limit: Maximum number of products to return.
            offset: Number of products to skip.

        Returns:
            List of products.
        """
        try:
            query = self.session.query(Product)
            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving products: {str(e)}')
            return []

        @inject(MaterialService)
            def search_by_name(self, name: str) -> List[Product]:
        """
        Search for products by name.

        Args:
            name: The name to search for.

        Returns:
            List of products that match the name.
        """
        try:
            return self.session.query(Product).filter(Product.name.ilike(
                f'%{name}%')).all()
        except SQLAlchemyError as e:
            logger.error(f"Error searching products by name '{name}': {str(e)}"
                         )
            return []

        @inject(MaterialService)
            def get_active_products(self) -> List[Product]:
        """
        Get active products.

        Returns:
            List of active products.
        """
        try:
            return self.session.query(Product).filter(Product.is_active == True
                                                      ).all()
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving active products: {str(e)}')
            return []

        @inject(MaterialService)
            def get_low_stock_products(self, include_zero_stock: bool = True) -> List[
                Product]:
        """
        Get products with low stock.

        Args:
            include_zero_stock: Whether to include products with zero stock.

        Returns:
            List of products with low stock.
        """
        try:
            query = self.session.query(Product).filter(Product.
                                                       stock_quantity <= Product.reorder_point)
            if not include_zero_stock:
                query = query.filter(Product.stock_quantity > 0)
            return query.all()
        except SQLAlchemyError as e:
            logger.error(f'Error retrieving low stock products: {str(e)}')
            return []

        @inject(MaterialService)
            def get_products_by_category(self, category: str) -> List[Product]:
        """
        Get products by material type (category).

        Args:
            category: The material type/category.

        Returns:
            List of products in the category.
        """
        try:
            return self.session.query(Product).filter(Product.material_type ==
                                                      category).all()
        except SQLAlchemyError as e:
            logger.error(
                f"Error retrieving products by category '{category}': {str(e)}"
            )
            return []

        @inject(MaterialService)
            def get_product_sales_summary(self) -> Dict[str, Any]:
        """
        Get a summary of product sales.

        Returns:
            Dictionary with product sales statistics.
        """
        try:
            total_products = self.session.query(Product).count()
            active_products = self.session.query(Product).filter(Product.
                                                                 is_active == True).count()
            low_stock_products = self.session.query(Product).filter(Product
                                                                    .stock_quantity <= Product.reorder_point).count()
            products = self.session.query(Product).all()
            total_margin = sum(product.calculate_profit_margin() for
                               product in products) if products else 0
            avg_margin = total_margin / len(products) if products else 0
            return {'total_products': total_products, 'active_products':
                    active_products, 'low_stock_products': low_stock_products,
                    'average_profit_margin': round(avg_margin, 2)}
        except SQLAlchemyError as e:
            logger.error(f'Error generating product sales summary: {str(e)}')
            return {'total_products': 0, 'active_products': 0,
                    'low_stock_products': 0, 'average_profit_margin': 0}
