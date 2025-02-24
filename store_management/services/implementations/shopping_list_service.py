from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
logger = logging.getLogger(__name__)


class ShoppingListService(IShoppingListService):
    """Implementation of shopping list management service."""

    @inject(MaterialService)
        def __init__(self, session_factory):
        """Initialize with session factory."""
        self.session_factory = session_factory

        @inject(MaterialService)
            def get_all_shopping_lists(self) -> List[ShoppingList]:
        """Get all shopping lists."""
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).all()
        except Exception as e:
            logger.error(f'Failed to get shopping lists: {str(e)}')
            raise ApplicationError('Failed to retrieve shopping lists', str(e))

        @inject(MaterialService)
            def get_shopping_list_by_id(self, list_id: int) -> Optional[ShoppingList]:
        """Get shopping list by ID."""
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(ShoppingList.id ==
                                                          list_id).first()
        except Exception as e:
            logger.error(f'Failed to get shopping list {list_id}: {str(e)}')
            raise ApplicationError(
                f'Failed to retrieve shopping list {list_id}', str(e))

        @inject(MaterialService)
            def create_shopping_list(self, list_data: Dict[str, Any]) -> ShoppingList:
        """Create new shopping list."""
        try:
            with self.session_factory() as session:
                self._validate_shopping_list_data(list_data)
                shopping_list = ShoppingList()
                for key, value in list_data.items():
                    if hasattr(shopping_list, key):
                        setattr(shopping_list, key, value)
                shopping_list.created_at = datetime.now()
                shopping_list.updated_at = datetime.now()
                shopping_list.status = ShoppingListStatus.ACTIVE
                session.add(shopping_list)
                session.commit()
                return shopping_list
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f'Failed to create shopping list: {str(e)}')
            raise ApplicationError('Failed to create shopping list', str(e))

        @inject(MaterialService)
            def update_shopping_list(self, list_id: int, list_data: Dict[str, Any]
                                 ) -> Optional[ShoppingList]:
        """Update existing shopping list."""
        try:
            with self.session_factory() as session:
                shopping_list = session.query(ShoppingList).filter(
                    ShoppingList.id == list_id).first()
                if not shopping_list:
                    return None
                self._validate_shopping_list_data(list_data)
                for key, value in list_data.items():
                    if hasattr(shopping_list, key):
                        setattr(shopping_list, key, value)
                shopping_list.updated_at = datetime.now()
                session.commit()
                return shopping_list
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f'Failed to update shopping list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to update shopping list {list_id}',
                                   str(e))

        @inject(MaterialService)
            def delete_shopping_list(self, list_id: int) -> bool:
        """Delete shopping list."""
        try:
            with self.session_factory() as session:
                shopping_list = session.query(ShoppingList).filter(
                    ShoppingList.id == list_id).first()
                if not shopping_list:
                    return False
                session.delete(shopping_list)
                session.commit()
                return True
        except Exception as e:
            logger.error(f'Failed to delete shopping list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to delete shopping list {list_id}',
                                   str(e))

        @inject(MaterialService)
            def add_item_to_list(self, list_id: int, item_data: Dict[str, Any]
                             ) -> ShoppingListItem:
        """Add item to shopping list."""
        try:
            with self.session_factory() as session:
                shopping_list = session.query(ShoppingList).filter(
                    ShoppingList.id == list_id).first()
                if not shopping_list:
                    raise ValidationError(f'Shopping list {list_id} not found')
                self._validate_item_data(item_data)
                item = ShoppingListItem()
                item.shopping_list_id = list_id
                for key, value in item_data.items():
                    if hasattr(item, key):
                        setattr(item, key, value)
                session.add(item)
                session.commit()
                return item
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f'Failed to add item to list {list_id}: {str(e)}')
            raise ApplicationError(f'Failed to add item to list', str(e))

        @inject(MaterialService)
            def remove_item_from_list(self, list_id: int, item_id: int) -> bool:
        """Remove item from shopping list."""
        try:
            with self.session_factory() as session:
                item = session.query(ShoppingListItem).filter(
                    ShoppingListItem.id == item_id, ShoppingListItem.
                    shopping_list_id == list_id).first()
                if not item:
                    return False
                session.delete(item)
                session.commit()
                return True
        except Exception as e:
            logger.error(
                f'Failed to remove item {item_id} from list {list_id}: {str(e)}'
            )
            raise ApplicationError('Failed to remove item from list', str(e))

        @inject(MaterialService)
            def mark_item_purchased(self, list_id: int, item_id: int, quantity: float
                                ) -> bool:
        """Mark item as purchased."""
        try:
            with self.session_factory() as session:
                item = session.query(ShoppingListItem).filter(
                    ShoppingListItem.id == item_id, ShoppingListItem.
                    shopping_list_id == list_id).first()
                if not item:
                    return False
                item.purchased_quantity = quantity
                item.purchase_date = datetime.now()
                session.commit()
                return True
        except Exception as e:
            logger.error(
                f'Failed to mark item {item_id} as purchased: {str(e)}')
            raise ApplicationError('Failed to mark item as purchased', str(e))

        @inject(MaterialService)
            def get_active_lists(self) -> List[ShoppingList]:
        """Get active shopping lists."""
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(ShoppingList.
                                                          status == ShoppingListStatus.ACTIVE).all()
        except Exception as e:
            logger.error(f'Failed to get active shopping lists: {str(e)}')
            raise ApplicationError('Failed to retrieve active lists', str(e))

        @inject(MaterialService)
            def get_pending_items(self) -> List[ShoppingListItem]:
        """Get pending items."""
        try:
            with self.session_factory() as session:
                return session.query(ShoppingListItem).filter(ShoppingListItem
                                                              .purchase_date.is_(None)).all()
        except Exception as e:
            logger.error(f'Failed to get pending items: {str(e)}')
            raise ApplicationError('Failed to retrieve pending items', str(e))

        @inject(MaterialService)
            def get_lists_by_status(self, status: str) -> List[ShoppingList]:
        """Get lists by status."""
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(ShoppingList.
                                                          status == status).all()
        except Exception as e:
            logger.error(f'Failed to get lists by status {status}: {str(e)}')
            raise ApplicationError(
                f'Failed to retrieve lists with status {status}', str(e))

        @inject(MaterialService)
            def search_shopping_lists(self, search_term: str) -> List[ShoppingList]:
        """Search shopping lists."""
        try:
            with self.session_factory() as session:
                return session.query(ShoppingList).filter(ShoppingList.name
                                                          .ilike(f'%{search_term}%')).all()
        except Exception as e:
            logger.error(f'Failed to search shopping lists: {str(e)}')
            raise ApplicationError('Failed to search shopping lists', str(e))

        @inject(MaterialService)
            def _validate_shopping_list_data(self, list_data: Dict[str, Any]) -> None:
        """Validate shopping list data."""
        errors = []
        if 'name' not in list_data or not list_data['name']:
            errors.append('Shopping list name is required')
        if errors:
            raise ValidationError('Shopping list validation failed', errors)

        @inject(MaterialService)
            def _validate_item_data(self, item_data: Dict[str, Any]) -> None:
        """Validate shopping list item data."""
        errors = []
        if 'name' not in item_data or not item_data['name']:
            errors.append('Item name is required')
        if 'quantity' in item_data:
            try:
                quantity = float(item_data['quantity'])
                if quantity <= 0:
                    errors.append('Quantity must be positive')
            except ValueError:
                errors.append('Invalid quantity value')
        if errors:
            raise ValidationError('Shopping list item validation failed',
                                  errors)
