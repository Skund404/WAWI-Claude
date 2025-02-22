# store_management/database/sqlalchemy/managers/incoming_goods_manager.py

from typing import List, Optional, Dict, Any
from datetime import datetime

from database.sqlalchemy.models import Order, OrderDetail, Supplier, Storage, Product
from database.sqlalchemy.models.order import OrderStatus, PaymentStatus
from database.sqlalchemy.session import get_session

class IncomingGoodsManager:
    def __init__(self):
        self.session = get_session()

    def create_order(self, data: Dict[str, Any]) -> Order:
        """Create a new order"""
        order = Order(
            order_number=data['order_number'],
            supplier=data['supplier'],
            date_of_order=datetime.strptime(data['date_of_order'], '%Y-%m-%d'),
            status=OrderStatus(data['status']),
            payed=PaymentStatus(data['payed']),
            total_amount=data['total_amount']
        )
        self.session.add(order)
        self.session.commit()
        return order

    def get_all_orders(self) -> List[Order]:
        """Get all orders"""
        return self.session.query(Order).all()

    def get_order_by_id(self, order_id: int) -> Optional[Order]:
        """Get an order by its ID"""
        return self.session.query(Order).get(order_id)

    def get_order_by_number(self, order_number: str) -> Optional[Order]:
        """Get an order by its order number"""
        return self.session.query(Order).filter_by(order_number=order_number).first()

    def update_order(self, order_id: int, data: Dict[str, Any]) -> bool:
        """Update an order"""
        order = self.get_order_by_id(order_id)
        if order:
            for key, value in data.items():
                setattr(order, key, value)
            self.session.commit()
            return True
        return False

    def delete_order(self, order_id: int) -> bool:
        """Delete an order"""
        order = self.get_order_by_id(order_id)
        if order:
            self.session.delete(order)
            self.session.commit()
            return True
        return False

    def add_order_detail(self, order_id: int, data: Dict[str, Any]) -> OrderDetail:
        """Add a detail to an order"""
        detail = OrderDetail(
            order_id=order_id,
            article=data['article'],
            unique_id=data['unique_id'],
            price=data['price'],
            amount=data['amount'],
            total=data['price'] * data['amount'],
            notes=data['notes']
        )
        self.session.add(detail)
        self.session.commit()
        return detail

    def get_order_details(self, order_id: int) -> List[OrderDetail]:
        """Get all details for an order"""
        return self.session.query(OrderDetail).filter_by(order_id=order_id).all()

    def update_order_detail(self, detail_id: int, data: Dict[str, Any]) -> bool:
        """Update an order detail"""
        detail = self.session.query(OrderDetail).get(detail_id)
        if detail:
            for key, value in data.items():
                setattr(detail, key, value)
            detail.total = detail.price * detail.amount
            self.session.commit()
            return True
        return False

    def delete_order_detail(self, detail_id: int) -> bool:
        """Delete an order detail"""
        detail = self.session.query(OrderDetail).get(detail_id)
        if detail:
            self.session.delete(detail)
            self.session.commit()
            return True
        return False

    def get_suppliers(self) -> List[str]:
        """Get a list of supplier names"""
        suppliers = self.session.query(Supplier.name).all()
        return [s[0] for s in suppliers]

    def update_inventory(self, unique_id: str, amount: int, is_shelf: bool):
        """Update inventory for a product"""
        if is_shelf:
            item = self.session.query(Storage).filter_by(unique_id=unique_id).first()
        else:
            item = self.session.query(Product).filter_by(unique_id=unique_id).first()

        if item:
            item.amount += amount
            self.session.commit()