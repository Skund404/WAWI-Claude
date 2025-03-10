# database/repositories/picking_list_item_repository.py
"""
Repository for Picking List Item entities.
"""

from database.repositories.base_repository import BaseRepository
from database.models.picking_list_item import PickingListItem

class PickingListItemRepository(BaseRepository):
    """
    Repository for managing Picking List Item database operations.
    """
    def __init__(self, session):
        """
        Initialize the Picking List Item Repository.

        Args:
            session: SQLAlchemy database session
        """
        super().__init__(session, PickingListItem)