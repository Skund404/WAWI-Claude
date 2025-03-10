#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/models/test_sales_purchases.py

import unittest
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Sales, SalesItem, Purchase, PurchaseItem,
    Customer, Product, Supplier, Material,
    SaleStatus, PaymentStatus, PurchaseStatus, CustomerStatus
)


class TestSalesModel(unittest.TestCase):
    """Test the Sales model implementation against ER diagram specifications."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

        # Setup test data
        cls.customer = Customer(
            name="Sales Test Customer",
            email="sales@example.com",
            status=CustomerStatus.ACTIVE
        )
        cls.session.add(cls.customer)
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_sales_schema(self):
        """Test that Sales model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('sales')}

        required_columns = {
            'id', 'customer_id', 'total_amount', 'status', 'payment_status',
            'notes', 'amount_paid', 'payment_date', 'shipping_address',
            'tracking_number', 'shipped_date', 'created_at', 'updated_at', 'cost_price'
        }
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in Sales model")

    def test_sales_relationships(self):
        """Test sales relationships match ER diagram."""
        # Create sales object
        sale = Sales(
            customer_id=self.customer.id,
            total_amount=100.0,
            status=SaleStatus.CONFIRMED,
            payment_status=PaymentStatus.PENDING
        )
        self.session.add(sale)
        self.session.commit()

        # Verify relationship attributes exist
        self.assertTrue(hasattr(sale, 'customer'), "Sales should have 'customer' relationship")
        self.assertTrue(hasattr(sale, 'items'), "Sales should have 'items' relationship")
        self.assertTrue(hasattr(sale, 'projects'), "Sales should have 'projects' relationship")
        self.assertTrue(hasattr(sale, 'picking_lists'), "Sales should have 'picking_lists' relationship")

    def test_sales_crud_and_validation(self):
        """Test CRUD operations and validation for Sales model."""
        sale = Sales(
            customer_id=self.customer.id,
            total_amount=150.0,
            status=SaleStatus.DRAFT
        )
        self.session.add(sale)
        self.session.commit()

        # Test validation
        with self.assertRaises(ValueError):
            sale.total_amount = -50.0
            sale.validate()

        # Reset to valid value
        sale.total_amount = 200.0
        self.session.commit()

        # Test read after update
        updated_sale = self.session.query(Sales).filter_by(id=sale.id).first()
        self.assertEqual(updated_sale.total_amount, 200.0)

# Additional test classes for SalesItem, Purchase, PurchaseItem would follow...
# (Truncated for brevity)