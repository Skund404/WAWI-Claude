#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/models/test_core_entities.py

import unittest
from datetime import datetime
import sys
import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Import the models to be tested
from models import (
    Base, Customer, Supplier, Material,
    Leather, Hardware, Thread,
    CustomerStatus, CustomerTier, CustomerSource,
    SupplierStatus, QualityGrade
)


class TestCustomerModel(unittest.TestCase):
    """Test the Customer model implementation against ER diagram specifications."""

    @classmethod
    def setUpClass(cls):
        """Create an in-memory SQLite database for testing."""
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

    @classmethod
    def tearDownClass(cls):
        """Close the session and drop all tables."""
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_customer_schema(self):
        """Test that Customer model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('customers')}

        required_columns = {'id', 'name', 'email', 'phone', 'address', 'status', 'tier', 'source', 'notes',
                            'is_business', 'created_at', 'updated_at'}
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in Customer model")

    def test_customer_relationships(self):
        """Test customer relationships match ER diagram."""
        # Create test data
        customer = Customer(
            name="Test Customer",
            email="test@example.com",
            status=CustomerStatus.ACTIVE
        )
        self.session.add(customer)
        self.session.commit()

        # Verify relationship attributes exist
        self.assertTrue(hasattr(customer, 'sales'), "Customer should have 'sales' relationship")

    def test_customer_crud(self):
        """Test CRUD operations for Customer model."""
        # Create
        customer = Customer(
            name="CRUD Test",
            email="crud@example.com",
            status=CustomerStatus.ACTIVE,
            tier=CustomerTier.STANDARD
        )
        self.session.add(customer)
        self.session.commit()

        # Read
        retrieved = self.session.query(Customer).filter_by(name="CRUD Test").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.email, "crud@example.com")

        # Update
        retrieved.email = "updated@example.com"
        self.session.commit()
        updated = self.session.query(Customer).filter_by(name="CRUD Test").first()
        self.assertEqual(updated.email, "updated@example.com")

        # Delete
        self.session.delete(updated)
        self.session.commit()
        deleted = self.session.query(Customer).filter_by(name="CRUD Test").first()
        self.assertIsNone(deleted)


class TestSupplierModel(unittest.TestCase):
    """Test the Supplier model implementation against ER diagram specifications."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_supplier_schema(self):
        """Test that Supplier model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('suppliers')}

        required_columns = {'id', 'name', 'contact_email', 'phone', 'address', 'status', 'created_at', 'updated_at'}
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in Supplier model")

    def test_supplier_relationships(self):
        """Test supplier relationships match ER diagram."""
        supplier = Supplier(
            name="Test Supplier",
            contact_email="supplier@example.com",
            status=SupplierStatus.ACTIVE
        )
        self.session.add(supplier)
        self.session.commit()

        # Verify relationship attributes exist
        self.assertTrue(hasattr(supplier, 'materials'), "Supplier should have 'materials' relationship")
        self.assertTrue(hasattr(supplier, 'purchases'), "Supplier should have 'purchases' relationship")

# Additional test classes for Material, Leather, Hardware, and Thread would follow...
# (Truncated for brevity)