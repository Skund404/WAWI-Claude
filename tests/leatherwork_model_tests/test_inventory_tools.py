#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/models/test_inventory_tools.py

import unittest
from datetime import datetime, timedelta
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Inventory, Material, Product, Tool,
    Leather, ToolList, ToolListItem,
    InventoryStatus, LeatherType, QualityGrade,
    TransactionType, InventoryAdjustmentType
)


class TestInventoryModel(unittest.TestCase):
    """Test the enhanced Inventory model implementation against ER diagram specifications."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

        # Setup test data
        cls.leather = Leather(
            name="Test Leather",
            leather_type=LeatherType.VEGETABLE_TANNED,
            quality=QualityGrade.PREMIUM,
            cost_price=100.0
        )
        cls.session.add(cls.leather)

        cls.product = Product(
            name="Test Wallet",
            description="A test wallet product",
            price=150.0,
            is_active=True
        )
        cls.session.add(cls.product)

        cls.tool = Tool(
            name="Test Tool",
            description="A test cutting tool",
            tool_type="CUTTING"
        )
        cls.session.add(cls.tool)

        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_inventory_schema(self):
        """Test that Inventory model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('inventory')}

        required_columns = {
            'id', 'item_type', 'item_id', 'quantity', 'status',
            'storage_location', 'created_at', 'updated_at',
            'min_stock_level', 'reorder_point', 'reorder_quantity',
            'location_details', 'last_count_date', 'last_movement_date',
            'transaction_history', 'unit_cost', 'notes'
        }
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in Inventory model")

    def test_inventory_for_material(self):
        """Test basic inventory tracking for material items."""
        # Create inventory for leather
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=5.0,
            status=InventoryStatus.IN_STOCK,
            storage_location="Shelf A1",
            min_stock_level=3.0,
            reorder_point=2.0,
            reorder_quantity=10.0,
            unit_cost=100.0
        )
        self.session.add(inventory)
        self.session.commit()

        # Test the relationship
        leather_from_db = self.session.query(Leather).filter_by(id=self.leather.id).first()
        self.assertIsNotNone(leather_from_db.inventory)
        self.assertEqual(leather_from_db.inventory.quantity, 5.0)

        # Test inventory update with transaction tracking
        inventory.update_quantity(
            change=2.0,
            transaction_type=TransactionType.PURCHASE,
            reference_type='purchase',
            reference_id=1,
            notes="Test purchase"
        )
        self.session.commit()

        updated_inventory = self.session.query(Inventory).filter_by(id=inventory.id).first()
        self.assertEqual(updated_inventory.quantity, 7.0)
        # Since 7.0 > min_stock_level (3.0) but <= 10.0, status should be LOW_STOCK
        self.assertEqual(updated_inventory.status, InventoryStatus.IN_STOCK)

        # Verify transaction history was recorded
        self.assertIsNotNone(updated_inventory.transaction_history)
        self.assertEqual(len(updated_inventory.transaction_history), 1)
        self.assertEqual(updated_inventory.transaction_history[0]['change'], 2.0)
        self.assertEqual(updated_inventory.transaction_history[0]['transaction_type'], TransactionType.PURCHASE.name)

    def test_inventory_status_updates(self):
        """Test inventory status updates based on thresholds."""
        inventory = Inventory(
            item_type='product',
            item_id=self.product.id,
            quantity=20.0,
            min_stock_level=5.0,
            reorder_point=10.0
        )
        self.session.add(inventory)
        self.session.commit()

        # Initially should be IN_STOCK as quantity (20) > reorder_point (10)
        self.assertEqual(inventory.status, InventoryStatus.IN_STOCK)

        # Reduce to 8 (below reorder_point but above min_stock_level)
        inventory.update_quantity(
            change=-12.0,
            transaction_type=TransactionType.USAGE,
            notes="Test usage"
        )
        self.session.commit()

        # Should be PENDING_REORDER
        self.assertEqual(inventory.quantity, 8.0)
        self.assertEqual(inventory.status, InventoryStatus.PENDING_REORDER)

        # Reduce to 4 (below min_stock_level)
        inventory.update_quantity(
            change=-4.0,
            transaction_type=TransactionType.USAGE,
            notes="Test usage"
        )
        self.session.commit()

        # Should be LOW_STOCK
        self.assertEqual(inventory.quantity, 4.0)
        self.assertEqual(inventory.status, InventoryStatus.LOW_STOCK)

        # Reduce to 0
        inventory.update_quantity(
            change=-4.0,
            transaction_type=TransactionType.USAGE,
            notes="Test usage"
        )
        self.session.commit()

        # Should be OUT_OF_STOCK
        self.assertEqual(inventory.quantity, 0.0)
        self.assertEqual(inventory.status, InventoryStatus.OUT_OF_STOCK)

    def test_inventory_adjustment(self):
        """Test inventory adjustment functionality."""
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=10.0,
            status=InventoryStatus.IN_STOCK
        )
        self.session.add(inventory)
        self.session.commit()

        # Record an adjustment
        inventory.record_adjustment(
            quantity_change=-2.0,
            adjustment_type=InventoryAdjustmentType.DAMAGE,
            reason="Material damaged during handling",
            authorized_by="Test User"
        )
        self.session.commit()

        # Verify quantity was updated
        self.assertEqual(inventory.quantity, 8.0)

        # Verify transaction was recorded
        self.assertEqual(len(inventory.transaction_history), 1)
        self.assertEqual(inventory.transaction_history[0]['transaction_type'], TransactionType.ADJUSTMENT.name)
        self.assertIn("DAMAGE", inventory.transaction_history[0]['notes'])
        self.assertIn("Test User", inventory.transaction_history[0]['notes'])

    def test_location_transfer(self):
        """Test inventory location transfer functionality."""
        inventory = Inventory(
            item_type='tool',
            item_id=self.tool.id,
            quantity=1.0,
            storage_location="Storage Room",
            location_details={"shelf": "B2", "container": "Red Box"}
        )
        self.session.add(inventory)
        self.session.commit()

        # Transfer to a new location
        inventory.transfer_location(
            new_location="Workshop",
            new_details={"shelf": "Tool Wall", "position": "Top Rack"},
            notes="Moved for current project"
        )
        self.session.commit()

        # Verify location was updated
        self.assertEqual(inventory.storage_location, "Workshop")
        self.assertEqual(inventory.location_details["shelf"], "Tool Wall")
        self.assertEqual(inventory.location_details["position"], "Top Rack")
        self.assertEqual(inventory.location_details["container"], "Red Box")  # Should keep old details not overwritten

        # Verify transaction was recorded
        self.assertEqual(len(inventory.transaction_history), 1)
        self.assertEqual(inventory.transaction_history[0]['transaction_type'], TransactionType.TRANSFER.name)
        self.assertEqual(inventory.transaction_history[0]['from_location'], "Storage Room")
        self.assertEqual(inventory.transaction_history[0]['to_location'], "Workshop")

    def test_physical_count(self):
        """Test physical inventory count functionality."""
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=5.0,
            status=InventoryStatus.IN_STOCK
        )
        self.session.add(inventory)
        self.session.commit()

        # Perform a physical count that finds more inventory than expected
        inventory.record_physical_count(
            counted_quantity=7.0,
            adjustment_notes="Found additional material behind shelf",
            counted_by="Test User"
        )
        self.session.commit()

        # Verify quantity was updated
        self.assertEqual(inventory.quantity, 7.0)

        # Verify last_count_date was updated
        self.assertIsNotNone(inventory.last_count_date)

        # Verify transaction was recorded
        self.assertEqual(len(inventory.transaction_history), 1)
        self.assertEqual(inventory.transaction_history[0]['transaction_type'], TransactionType.ADJUSTMENT.name)
        self.assertEqual(inventory.transaction_history[0]['change'], 2.0)

        # Perform a physical count that finds less inventory than expected
        inventory.record_physical_count(
            counted_quantity=6.0,
            adjustment_notes="Some material appears to be missing",
            counted_by="Test User"
        )
        self.session.commit()

        # Verify quantity was updated again
        self.assertEqual(inventory.quantity, 6.0)

        # Verify transactions stack in history
        self.assertEqual(len(inventory.transaction_history), 2)

    def test_transaction_history_limit(self):
        """Test that transaction history maintains limited entries."""
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=100.0
        )
        self.session.add(inventory)
        self.session.commit()

        # Create 15 transactions (more than the 10 limit)
        for i in range(15):
            inventory.update_quantity(
                change=-1.0,
                transaction_type=TransactionType.USAGE,
                notes=f"Usage {i + 1}"
            )
            self.session.commit()

        # Verify only the 10 most recent transactions are kept
        self.assertEqual(len(inventory.transaction_history), 10)

        # Verify the oldest transactions were dropped
        for i in range(10):
            self.assertEqual(inventory.transaction_history[i]['notes'], f"Usage {i + 6}")

    def test_calculate_value(self):
        """Test inventory value calculation."""
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=5.0,
            unit_cost=100.0
        )
        self.session.add(inventory)
        self.session.commit()

        # Test value calculation
        self.assertEqual(inventory.calculate_value(), 500.0)

        # Update quantity and verify value changes
        inventory.update_quantity(
            change=2.0,
            transaction_type=TransactionType.PURCHASE
        )
        self.session.commit()

        self.assertEqual(inventory.calculate_value(), 700.0)

    def test_needs_reorder(self):
        """Test reorder need detection."""
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=15.0,
            reorder_point=10.0
        )
        self.session.add(inventory)
        self.session.commit()

        # Initially above reorder point
        self.assertFalse(inventory.needs_reorder())

        # Reduce below reorder point
        inventory.update_quantity(
            change=-6.0,
            transaction_type=TransactionType.USAGE
        )
        self.session.commit()

        # Should now need reorder
        self.assertTrue(inventory.needs_reorder())

    def test_negative_quantity_validation(self):
        """Test that negative quantities are rejected."""
        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=5.0
        )
        self.session.add(inventory)
        self.session.commit()

        # Attempt to reduce quantity below zero
        with self.assertRaises(Exception):
            inventory.update_quantity(
                change=-10.0,
                transaction_type=TransactionType.USAGE
            )

    def test_days_calculation(self):
        """Test calculation of days since last count/movement."""
        # Set timestamps to a known past date
        past_date = datetime.now() - timedelta(days=10)

        inventory = Inventory(
            item_type='material',
            item_id=self.leather.id,
            quantity=5.0,
            last_count_date=past_date,
            last_movement_date=past_date
        )
        self.session.add(inventory)
        self.session.commit()

        # Should be approximately 10 days
        self.assertGreaterEqual(inventory.days_since_last_count(), 10)
        self.assertLess(inventory.days_since_last_count(), 11)

        self.assertGreaterEqual(inventory.days_since_last_movement(), 10)
        self.assertLess(inventory.days_since_last_movement(), 11)

        # Update with movement and verify last_movement_date changes
        inventory.update_quantity(
            change=1.0,
            transaction_type=TransactionType.PURCHASE
        )
        self.session.commit()

        # Movement date should be reset
        self.assertLessEqual(inventory.days_since_last_movement(), 0)

        # Count date should still be 10 days
        self.assertGreaterEqual(inventory.days_since_last_count(), 10)

# Additional test classes for ToolList, ToolListItem would follow...
# (Truncated for brevity)