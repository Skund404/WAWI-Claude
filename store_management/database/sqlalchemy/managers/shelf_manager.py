from typing import List, Optional, Dict, Any
from sqlalchemy import select  # Change from sqlalchemy.select to sqlalchemy
from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.database.sqlalchemy.models import Shelf
from store_management.utils.error_handler import DatabaseError
from store_management.utils.logger import logger

class ShelfManager(BaseManager):
    """
    Enhanced shelf manager implementing specialized shelf operations
    while leveraging base manager functionality.
    """

    def __init__(self, session_factory):
        super().__init__(session_factory, Shelf)

    def get_shelf_with_items(self, shelf_id: int) -> Optional[Shelf]:
        """
        Get shelf with associated leather items.

        Args:
            shelf_id: Shelf ID

        Returns:
            Shelf instance with leather items loaded or None if not found
        """
        query = select(Shelf).where(Shelf.id == shelf_id).options(joinedload(Shelf.leather_items))
        with self.session_scope() as session:
            return session.execute(query).scalars().one_or_none()

    def search_shelves(self, term: str) -> List[Shelf]:
        """
        Search shelves by name or location.

        Args:
            term: Search term

        Returns:
            List of matching Shelf instances
        """
        query = select(Shelf).where(
            func.lower(Shelf.name).contains(term.lower()) |
            func.lower(Shelf.location).contains(term.lower())
        )
        with self.session_scope() as session:
            return list(session.execute(query).scalars())

    def update_multiple_shelves(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple shelves in a single transaction.

        Args:
            updates: List of shelf updates as dictionaries

        Returns:
            Number of shelves updated
        """
        with self.session_scope() as session:
            session.bulk_update_mappings(Shelf, updates)
            return len(updates)

    def add_shelf(self, data: Dict[str, Any]) -> Optional[Shelf]:
        """
        Add a new shelf.

        Args:
            data: Dictionary containing shelf data

        Returns:
            Created Shelf instance or None if creation fails

        Raises:
            DatabaseError: If validation fails or database operation fails
        """
        try:
            # Validate required fields
            required_fields = ['name', 'location']
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise DatabaseError(f"Missing required fields: {', '.join(missing_fields)}")

            # Create shelf
            shelf = self.create(data)
            return shelf

        except SQLAlchemyError as e:
            logger.error(f"Failed to add shelf: {str(e)}")
            raise DatabaseError(f"Failed to add shelf: {str(e)}") from e