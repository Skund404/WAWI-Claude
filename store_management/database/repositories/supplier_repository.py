from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from database.interfaces.base_repository import BaseRepository
from database.models.supplier import Supplier
from database.models.order import Order
from utils.error_handler import DatabaseError, ValidationError


class SupplierRepository(BaseRepository):
    """
    Repository for managing supplier-related database operations.

    Provides specialized methods for retrieving, creating, and managing
    supplier information with advanced querying capabilities.
    """

    def __init__(self, session: Session):
        """
        Initialize the SupplierRepository with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Supplier)

    def search(self, search_term: str,
               fields: List[str] = None,
               limit: int = 10) -> List[Supplier]:
        """
        Search for suppliers using a flexible search across multiple fields.

        Args:
            search_term (str): Term to search for
            fields (Optional[List[str]]): Specific fields to search
            limit (int, optional): Maximum number of results. Defaults to 10.

        Returns:
            List of Supplier instances matching the search criteria
        """
        try:
            # Default search fields if not specified
            if not fields:
                fields = ['name', 'email', 'phone', 'address']

            # Prepare search conditions
            search_conditions = []
            normalized_term = f"%{search_term.lower().strip()}%"

            for field in fields:
                # Dynamically create search conditions for each field
                model_field = getattr(Supplier, field, None)
                if model_field is not None:
                    search_conditions.append(func.lower(model_field).like(normalized_term))

            # Execute search query
            query = self.session.query(Supplier).filter(or_(*search_conditions)).limit(limit)
            return query.all()

        except Exception as e:
            raise DatabaseError(f"Error searching suppliers: {str(e)}")

    def get_supplier_orders(self,
                            supplier_id: int,
                            start_date: Optional[datetime] = None,
                            end_date: Optional[datetime] = None) -> List[Order]:
        """
        Retrieve orders associated with a specific supplier.

        Args:
            supplier_id (int): ID of the supplier
            start_date (Optional[datetime]): Start of order date range
            end_date (Optional[datetime]): End of order date range

        Returns:
            List of Order instances
        """
        try:
            # Default to last 90 days if no dates provided
            if not start_date:
                start_date = datetime.now() - timedelta(days=90)
            if not end_date:
                end_date = datetime.now()

            # Construct query
            query = (
                self.session.query(Order)
                .filter(Order.supplier_id == supplier_id)
                .filter(Order.order_date.between(start_date, end_date))
            )

            return query.all()

        except Exception as e:
            raise DatabaseError(f"Error retrieving supplier orders: {str(e)}")

    def get_top_suppliers(self,
                          limit: int = 10,
                          performance_metric: str = 'completed_orders') -> List[Dict[str, Any]]:
        """
        Retrieve top suppliers based on a specific performance metric.

        Args:
            limit (int, optional): Number of top suppliers to return. Defaults to 10.
            performance_metric (str, optional): Metric to rank suppliers. Defaults to 'completed_orders'.

        Returns:
            List of dictionaries with supplier information and performance metrics
        """
        try:
            # Subquery to get supplier performance
            performance_subquery = (
                self.session.query(
                    Order.supplier_id,
                    func.count(Order.id).label('total_orders'),
                    func.sum(
                        func.case(
                            [(Order.status == 'COMPLETED', 1)],
                            else_=0
                        )
                    ).label('completed_orders')
                )
                .group_by(Order.supplier_id)
                .subquery()
            )

            # Join suppliers with performance metrics
            query = (
                self.session.query(
                    Supplier,
                    performance_subquery.c.total_orders,
                    performance_subquery.c.completed_orders
                )
                .outerjoin(
                    performance_subquery,
                    Supplier.id == performance_subquery.c.supplier_id
                )
                .order_by(performance_subquery.c.completed_orders.desc().nulls_last())
                .limit(limit)
            )

            # Transform results
            top_suppliers = []
            for supplier, total_orders, completed_orders in query:
                supplier_dict = supplier.to_dict()
                supplier_dict['total_orders'] = total_orders or 0
                supplier_dict['completed_orders'] = completed_orders or 0

                # Calculate completion rate
                supplier_dict['completion_rate'] = (
                    (completed_orders / total_orders * 100) if total_orders else 0
                )

                top_suppliers.append(supplier_dict)

            return top_suppliers

        except Exception as e:
            raise DatabaseError(f"Error retrieving top suppliers: {str(e)}")

    def create(self, data: Dict[str, Any]) -> Supplier:
        """
        Create a new supplier record with additional validation.

        Args:
            data (Dict[str, Any]): Supplier creation data

        Returns:
            Supplier: Created supplier instance

        Raises:
            ValidationError: If data is invalid
            DatabaseError: For database-related errors
        """
        try:
            # Validate required fields
            if not data.get('name'):
                raise ValidationError("Supplier name is required")

            # Check for existing supplier with the same name
            existing_supplier = self.search(data['name'], fields=['name'])
            if existing_supplier:
                raise ValidationError(f"Supplier with name '{data['name']}' already exists")

            # Create supplier instance
            supplier = Supplier(**data)

            # Add to session and commit
            self.session.add(supplier)
            self.session.commit()

            return supplier

        except (ValidationError, DatabaseError):
            # Re-raise validation errors
            raise
        except Exception as e:
            # Rollback session on unexpected errors
            self.session.rollback()
            raise DatabaseError(f"Error creating supplier: {str(e)}")

    def update(self, supplier_id: int, data: Dict[str, Any]) -> Supplier:
        """
        Update an existing supplier record.

        Args:
            supplier_id (int): ID of the supplier to update
            data (Dict[str, Any]): Update data

        Returns:
            Supplier: Updated supplier instance

        Raises:
            ValidationError: If data is invalid
            DatabaseError: For database-related errors
        """
        try:
            # Retrieve existing supplier
            supplier = self.get(supplier_id)
            if not supplier:
                raise ValidationError(f"Supplier with ID {supplier_id} not found")

            # Update supplier attributes
            for key, value in data.items():
                setattr(supplier, key, value)

            # Commit changes
            self.session.commit()

            return supplier

        except (ValidationError, DatabaseError):
            # Re-raise validation errors
            raise
        except Exception as e:
            # Rollback session on unexpected errors
            self.session.rollback()
            raise DatabaseError(f"Error updating supplier: {str(e)}")

    def delete(self, supplier_id: int) -> bool:
        """
        Delete a supplier record after checking for dependencies.

        Args:
            supplier_id (int): ID of the supplier to delete

        Returns:
            bool: True if deletion was successful

        Raises:
            ValidationError: If supplier has active dependencies
            DatabaseError: For database-related errors
        """
        try:
            # Check for existing orders
            existing_orders = (
                self.session.query(Order)
                .filter(Order.supplier_id == supplier_id)
                .count()
            )

            if existing_orders > 0:
                raise ValidationError(
                    f"Cannot delete supplier {supplier_id}. "
                    "Existing orders prevent deletion."
                )

            # Retrieve and delete supplier
            supplier = self.get(supplier_id)
            if not supplier:
                raise ValidationError(f"Supplier with ID {supplier_id} not found")

            self.session.delete(supplier)
            self.session.commit()

            return True

        except (ValidationError, DatabaseError):
            # Re-raise validation errors
            raise
        except Exception as e:
            # Rollback session on unexpected errors
            self.session.rollback()
            raise DatabaseError(f"Error deleting supplier: {str(e)}")