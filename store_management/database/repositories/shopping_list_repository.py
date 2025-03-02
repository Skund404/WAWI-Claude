# database/repositories/shopping_list_repository.py
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import SQLAlchemyError

from database.models.shopping_list import ShoppingList, ShoppingListItem
from database.models.enums import ShoppingListStatus, Priority
from database.repositories.base_repository import BaseRepository

import logging
from typing import List, Optional, Dict, Any, Union
from datetime import datetime


class ShoppingListRepository(BaseRepository):
    """
    Repository for managing Shopping List database operations.

    Provides methods for:
    - CRUD operations on Shopping List entities
    - Advanced querying capabilities
    - Detailed reporting and analytics
    - Error handling and logging
    """

    def __init__(self, session: Session):
        """
        Initialize the Shopping List Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, ShoppingList)
        self.logger = logging.getLogger(self.__class__.__name__)

    def search_shopping_lists(self,
                              search_term: Optional[str] = None,
                              status: Optional[ShoppingListStatus] = None,
                              priority: Optional[Priority] = None,
                              is_completed: Optional[bool] = None,
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> List[ShoppingList]:
        """
        Advanced search for shopping lists with multiple filtering options.

        Args:
            search_term (Optional[str]): Search across name and description
            status (Optional[ShoppingListStatus]): Filter by shopping list status
            priority (Optional[Priority]): Filter by priority
            is_completed (Optional[bool]): Filter by completion status
            start_date (Optional[datetime]): Earliest creation date
            end_date (Optional[datetime]): Latest creation date

        Returns:
            List[ShoppingList]: List of shopping lists matching the search criteria
        """
        try:
            query = self.session.query(ShoppingList)

            # Name/description search
            if search_term:
                search_filter = or_(
                    ShoppingList.name.ilike(f"%{search_term}%"),
                    ShoppingList.description.ilike(f"%{search_term}%")
                )
                query = query.filter(search_filter)

            # Status filter
            if status:
                query = query.filter(ShoppingList.status == status)

            # Priority filter
            if priority:
                query = query.filter(ShoppingList.priority == priority)

            # Completion status filter
            if is_completed is not None:
                query = query.filter(ShoppingList.is_completed == is_completed)

            # Date range filter
            if start_date:
                query = query.filter(ShoppingList.created_at >= start_date)

            if end_date:
                query = query.filter(ShoppingList.created_at <= end_date)

            # Eager load items to reduce additional queries
            query = query.options(joinedload(ShoppingList.items))

            # Execute query and log results
            results = query.all()

            self.logger.info("Shopping list search completed", extra={
                "search_term": search_term,
                "status": status,
                "priority": priority,
                "is_completed": is_completed,
                "start_date": start_date,
                "end_date": end_date,
                "results_count": len(results)
            })

            return results

        except SQLAlchemyError as e:
            self.logger.error(f"Error searching shopping lists: {str(e)}", extra={
                "search_params": {
                    "search_term": search_term,
                    "status": status,
                    "priority": priority,
                    "is_completed": is_completed,
                    "start_date": start_date,
                    "end_date": end_date
                },
                "error": str(e)
            })
            return []

    def get_shopping_list_with_items(self, shopping_list_id: int) -> Optional[ShoppingList]:
        """
        Retrieve a shopping list with all its items.

        Args:
            shopping_list_id (int): ID of the shopping list

        Returns:
            Optional[ShoppingList]: Shopping list with loaded items, or None if not found
        """
        try:
            shopping_list = (self.session.query(ShoppingList)
                             .options(joinedload(ShoppingList.items))
                             .filter(ShoppingList.id == shopping_list_id)
                             .first())

            if shopping_list:
                self.logger.info("Shopping list retrieved with items", extra={
                    "shopping_list_id": shopping_list_id,
                    "item_count": len(shopping_list.items)
                })

            return shopping_list

        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving shopping list with items: {str(e)}", extra={
                "shopping_list_id": shopping_list_id,
                "error": str(e)
            })
            return None

    def get_shopping_list_analytics(self,
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Generate comprehensive analytics for shopping lists.

        Args:
            start_date (Optional[datetime]): Start of the analysis period
            end_date (Optional[datetime]): End of the analysis period

        Returns:
            Dict[str, Any]: Detailed shopping list analytics
        """
        try:
            # Base query
            query = self.session.query(ShoppingList)

            # Apply date range if provided
            if start_date:
                query = query.filter(ShoppingList.created_at >= start_date)
            if end_date:
                query = query.filter(ShoppingList.created_at <= end_date)

            # Aggregate queries
            total_lists = query.count()
            completed_lists = query.filter(ShoppingList.is_completed == True).count()

            # Priority distribution
            priority_distribution = {}
            for priority in Priority:
                priority_count = query.filter(ShoppingList.priority == priority).count()
                priority_distribution[priority.name] = priority_count

            # Status distribution
            status_distribution = {}
            for status in ShoppingListStatus:
                status_count = query.filter(ShoppingList.status == status).count()
                status_distribution[status.name] = status_count

            # Total estimated cost for all lists
            total_estimated_cost = self.session.query(
                func.sum(
                    func.coalesce(
                        ShoppingListItem.quantity *
                        func.coalesce(ShoppingListItem.estimated_price, 0),
                        0
                    )
                )
                .select_from(ShoppingList)
                .join(ShoppingListItem, isouter=True)
                .filter(query.whereclause)
            ).scalar() or 0

            # Prepare analytics result
            analytics = {
                "total_lists": total_lists,
                "completed_lists": completed_lists,
                "completion_rate": (completed_lists / total_lists) * 100 if total_lists > 0 else 0,
                "total_estimated_cost": total_estimated_cost,
                "priority_distribution": priority_distribution,
                "status_distribution": status_distribution
            }

            self.logger.info("Shopping list analytics generated", extra={
                "total_lists": total_lists,
                "completed_lists": completed_lists,
                "total_estimated_cost": total_estimated_cost
            })

            return analytics

        except SQLAlchemyError as e:
            self.logger.error(f"Error generating shopping list analytics: {str(e)}", extra={
                "start_date": start_date,
                "end_date": end_date,
                "error": str(e)
            })
            return {
                "total_lists": 0,
                "completed_lists": 0,
                "completion_rate": 0,
                "total_estimated_cost": 0,
                "priority_distribution": {},
                "status_distribution": {}
            }