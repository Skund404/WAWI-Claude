# database/repositories/supplier_repository.py
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional, Type, Tuple
from datetime import datetime, timedelta
from sqlalchemy import func, or_, and_, desc

from database.repositories.base_repository import BaseRepository, EntityNotFoundError, ValidationError, RepositoryError
from database.models.enums import SupplierStatus


class SupplierRepository(BaseRepository):
    """Repository for supplier operations.

    This repository provides methods for querying and manipulating supplier data,
    including relationships with materials, tools, and purchases.
    """

    def _get_model_class(self) -> Type:
        """Return the model class this repository manages.

        Returns:
            The Supplier model class
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier
        return Supplier

    # Supplier-specific query methods

    def get_by_status(self, status: SupplierStatus) -> List:
        """Get suppliers by status.

        Args:
            status: Supplier status to filter by

        Returns:
            List of supplier instances with the specified status
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier

        self.logger.debug(f"Getting suppliers with status '{status.value}'")
        return self.session.query(Supplier).filter(Supplier.status == status).all()

    def get_by_name(self, name: str) -> List:
        """Get suppliers by name (partial match).

        Args:
            name: Name to search for

        Returns:
            List of supplier instances matching the name
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier

        self.logger.debug(f"Getting suppliers with name containing '{name}'")
        return self.session.query(Supplier).filter(Supplier.name.like(f"%{name}%")).all()

    def get_by_email(self, email: str) -> Optional:
        """Get supplier by exact email address.

        Args:
            email: Email address to search for

        Returns:
            Supplier instance with the specified email or None
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier

        self.logger.debug(f"Getting supplier with email '{email}'")
        return self.session.query(Supplier).filter(Supplier.contact_email == email).first()

    def get_active_suppliers(self) -> List:
        """Get all active suppliers.

        Returns:
            List of active supplier instances
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier

        self.logger.debug("Getting all active suppliers")
        return self.session.query(Supplier).filter(Supplier.status == SupplierStatus.ACTIVE).all()

    def get_suppliers_with_purchases(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get suppliers with their purchase history.

        Args:
            limit: Maximum number of suppliers to return

        Returns:
            List of suppliers with purchase history
        """
        # Import at function level to avoid circular imports
        from database.models.purchase import Purchase

        self.logger.debug(f"Getting suppliers with purchases (limit: {limit})")

        suppliers = self.get_all(limit=limit)
        result = []

        for supplier in suppliers:
            supplier_dict = supplier.to_dict()

            # Get purchase history
            purchases = self.session.query(Purchase).filter(
                Purchase.supplier_id == supplier.id
            ).order_by(Purchase.created_at.desc()).all()

            supplier_dict['purchases'] = [p.to_dict() for p in purchases]
            supplier_dict['total_purchases'] = len(purchases)
            supplier_dict['total_spent'] = sum(p.total_amount for p in purchases)

            if purchases:
                supplier_dict['last_purchase_date'] = purchases[0].created_at.isoformat()
            else:
                supplier_dict['last_purchase_date'] = None

            result.append(supplier_dict)

        return result

    # Business logic methods

    def get_supplier_performance(self, supplier_id: int) -> Dict[str, Any]:
        """Get supplier performance metrics.

        Args:
            supplier_id: ID of the supplier

        Returns:
            Dict with performance metrics

        Raises:
            EntityNotFoundError: If supplier not found
        """
        # Import at function level to avoid circular imports
        from database.models.purchase import Purchase
        from database.models.material import Material
        from database.models.tool import Tool

        self.logger.debug(f"Getting performance metrics for supplier {supplier_id}")

        supplier = self.get_by_id(supplier_id)
        if not supplier:
            raise EntityNotFoundError(f"Supplier with ID {supplier_id} not found")

        # Get all purchases
        purchases = self.session.query(Purchase).filter(
            Purchase.supplier_id == supplier_id
        ).all()

        if not purchases:
            return {
                'supplier_id': supplier_id,
                'supplier_name': supplier.name,
                'total_purchases': 0,
                'total_spent': 0,
                'avg_lead_time': None,
                'on_time_delivery_rate': None,
                'last_purchase_date': None,
                'materials_supplied': [],
                'tools_supplied': []
            }

        # Calculate metrics
        total_spent = sum(p.total_amount for p in purchases)

        # Calculate lead time (days between order and delivery)
        lead_times = []
        on_time_deliveries = 0

        for p in purchases:
            if p.created_at and p.delivery_date:
                lead_time = (p.delivery_date - p.created_at).days
                lead_times.append(lead_time)

                # Assume on-time delivery if within 2 days of expected date
                if p.expected_delivery_date:
                    if p.delivery_date <= p.expected_delivery_date + timedelta(days=2):
                        on_time_deliveries += 1

        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else None
        on_time_delivery_rate = on_time_deliveries / len(purchases) * 100 if purchases else None

        # Get supplied materials
        materials = self.session.query(Material).filter(
            Material.supplier_id == supplier_id
        ).all()

        # Get supplied tools
        tools = self.session.query(Tool).filter(
            Tool.supplier_id == supplier_id
        ).all()

        return {
            'supplier_id': supplier_id,
            'supplier_name': supplier.name,
            'total_purchases': len(purchases),
            'total_spent': total_spent,
            'avg_lead_time': avg_lead_time,
            'on_time_delivery_rate': on_time_delivery_rate,
            'last_purchase_date': max(p.created_at for p in purchases).isoformat(),
            'materials_supplied': [m.to_dict() for m in materials],
            'tools_supplied': [t.to_dict() for t in tools]
        }

    def get_material_suppliers(self, material_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get suppliers that provide specific types of materials.

        Args:
            material_type: Optional material type to filter by

        Returns:
            List of suppliers with material counts
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier
        from database.models.material import Material

        self.logger.debug(f"Getting material suppliers for type '{material_type}'")

        query = self.session.query(
            Supplier,
            func.count(Material.id).label('material_count')
        ).join(
            Material,
            Material.supplier_id == Supplier.id
        )

        if material_type:
            query = query.filter(Material.material_type == material_type)

        query = query.group_by(Supplier.id)

        result = []
        for supplier, material_count in query.all():
            supplier_dict = supplier.to_dict()
            supplier_dict['material_count'] = material_count
            result.append(supplier_dict)

        return result

    # GUI-specific functionality

    def get_supplier_dashboard_data(self) -> Dict[str, Any]:
        """Get data for supplier dashboard in GUI.

        Returns:
            Dictionary with dashboard data for suppliers
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier
        from database.models.purchase import Purchase

        self.logger.debug("Getting supplier dashboard data")

        # Count by status
        status_counts = self.session.query(
            Supplier.status,
            func.count().label('count')
        ).group_by(Supplier.status).all()

        status_data = {s.value: count for s, count in status_counts}

        # Get total number of suppliers
        total_suppliers = self.count()

        # Get top suppliers by purchase amount
        top_suppliers_query = self.session.query(
            Supplier.id,
            Supplier.name,
            Supplier.status,
            func.sum(Purchase.total_amount).label('total_spent')
        ).join(
            Purchase,
            Purchase.supplier_id == Supplier.id
        ).group_by(
            Supplier.id,
            Supplier.name,
            Supplier.status
        ).order_by(
            func.sum(Purchase.total_amount).desc()
        ).limit(5)

        top_suppliers = []
        for id, name, status, total_spent in top_suppliers_query.all():
            top_suppliers.append({
                'id': id,
                'name': name,
                'status': status.value,
                'total_spent': total_spent
            })

        # Get recent purchases
        recent_purchases_query = self.session.query(Purchase).order_by(
            Purchase.created_at.desc()
        ).limit(5)

        recent_purchases = []
        for purchase in recent_purchases_query.all():
            purchase_dict = purchase.to_dict()

            # Add supplier name
            supplier = self.get_by_id(purchase.supplier_id)
            if supplier:
                purchase_dict['supplier_name'] = supplier.name

            recent_purchases.append(purchase_dict)

        return {
            'status_counts': status_data,
            'total_suppliers': total_suppliers,
            'top_suppliers': top_suppliers,
            'recent_purchases': recent_purchases
        }

    def generate_supplier_report(self, start_date: Optional[datetime] = None,
                                 end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """Generate comprehensive supplier report.

        Args:
            start_date: Optional start date for filtering
            end_date: Optional end date for filtering

        Returns:
            Dict with supplier report data
        """
        # Import at function level to avoid circular imports
        from database.models.supplier import Supplier
        from database.models.purchase import Purchase
        from database.models.material import Material

        self.logger.debug(f"Generating supplier report (start: {start_date}, end: {end_date})")

        # Default date range is last 12 months if not specified
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)

        # Get suppliers and their metrics
        suppliers = self.get_all(limit=1000)  # Get all suppliers

        supplier_data = []
        total_spent = 0
        total_orders = 0
        material_count_by_type = {}

        for supplier in suppliers:
            # Get purchases in date range
            purchases = self.session.query(Purchase).filter(
                Purchase.supplier_id == supplier.id,
                Purchase.created_at >= start_date,
                Purchase.created_at <= end_date
            ).all()

            supplier_spent = sum(p.total_amount for p in purchases)
            total_spent += supplier_spent
            total_orders += len(purchases)

            # Get materials from this supplier
            materials = self.session.query(Material).filter(
                Material.supplier_id == supplier.id
            ).all()

            # Count materials by type
            for material in materials:
                material_type = material.material_type.value
                if material_type not in material_count_by_type:
                    material_count_by_type[material_type] = 0
                material_count_by_type[material_type] += 1

            # Add to report data if they have any purchases
            if purchases:
                supplier_data.append({
                    'id': supplier.id,
                    'name': supplier.name,
                    'status': supplier.status.value,
                    'contact_email': supplier.contact_email,
                    'total_spent': supplier_spent,
                    'order_count': len(purchases),
                    'material_count': len(materials),
                    'average_order_value': supplier_spent / len(purchases) if len(purchases) > 0 else 0
                })

        # Sort by total spent descending
        supplier_data.sort(key=lambda x: x['total_spent'], reverse=True)

        # Create report
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'summary': {
                'total_suppliers': len(suppliers),
                'active_suppliers': len([s for s in suppliers if s.status == SupplierStatus.ACTIVE]),
                'total_spent': total_spent,
                'total_orders': total_orders,
                'material_types': material_count_by_type
            },
            'supplier_data': supplier_data
        }