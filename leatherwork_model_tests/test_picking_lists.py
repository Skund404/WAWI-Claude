#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/models/test_picking_lists.py

import unittest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from models import (
    Base, PickingList, PickingListItem,
    Sales, Customer, Component, Material,
    PickingListStatus, SaleStatus, ComponentType
)


class TestPickingListModel(unittest.TestCase):
    """Test the PickingList model implementation against ER diagram specifications."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

        # Setup test data
        cls.customer = Customer(name="Picking Test Customer", email="picking@example.com")
        cls.session.add(cls.customer)

        cls.sale = Sales(
            customer_id=1,  # Will be set after customer is committed
            total_amount=200.0,
            status=SaleStatus.CONFIRMED
        )

        cls.component = Component(
            name="Test Component",
            component_type=ComponentType.LEATHER,
        )

        cls.material = Material(
            name="Test Material",
            material_type="generic",
        )

        cls.session.add_all([cls.customer, cls.sale, cls.component, cls.material])
        cls.session.commit()

        # Update the sale with correct customer ID
        cls.sale.customer_id = cls.customer.id
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_picking_list_schema(self):
        """Test that PickingList model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('picking_lists')}

        required_columns = {
            'id', 'sales_id', 'status', 'completed_at',
            'notes', 'created_at', 'updated_at'
        }
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in PickingList model")

    def test_picking_list_item_schema(self):
        """Test that PickingListItem model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('picking_list_items')}

        required_columns = {
            'id', 'picking_list_id', 'component_id', 'material_id',
            'quantity_ordered', 'quantity_picked', 'created_at', 'updated_at'
        }
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in PickingListItem model")

    def test_picking_list_relationships(self):
        """Test picking list relationships match ER diagram."""
        picking_list = PickingList(
            sales_id=self.sale.id,
            status=PickingListStatus.DRAFT
        )
        self.session.add(picking_list)
        self.session.commit()

        # Create picking list items
        item1 = PickingListItem(
            picking_list_id=picking_list.id,
            component_id=self.component.id,
            quantity_ordered=2,
            quantity_picked=0
        )

        item2 = PickingListItem(
            picking_list_id=picking_list.id,
            material_id=self.material.id,
            quantity_ordered=5,
            quantity_picked=0
        )

        self.session.add_all([item1, item2])
        self.session.commit()

        # Test relationships
        picking_list_from_db = self.session.query(PickingList).filter_by(id=picking_list.id).first()
        self.assertEqual(len(picking_list_from_db.items), 2)
        self.assertEqual(picking_list_from_db.sale.id, self.sale.id)

        # Test is_complete method
        self.assertFalse(picking_list.is_complete())

        # Update items to be fully picked
        for item in picking_list.items:
            item.quantity_picked = item.quantity_ordered
        self.session.commit()

        # Check completion status again
        self.assertTrue(picking_list.is_complete())

# Additional test methods for PickingListItem would follow...
# (Truncated for brevity)