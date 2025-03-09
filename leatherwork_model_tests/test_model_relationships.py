#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/models/test_model_relationships.py

import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Customer, Sales, SalesItem, Product, Pattern,
    Component, ComponentMaterial, Material, Supplier,
    Project, ProjectComponent, PickingList, PickingListItem,
    ToolList, ToolListItem, Purchase, PurchaseItem,
    Inventory, Leather, Hardware, Thread,
    SaleStatus, PaymentStatus, ProjectType, ProjectStatus,
    ComponentType, LeatherType, HardwareType
)


class TestMaterialRelationships(unittest.TestCase):
    """Test the relationships involving Material models."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

        # Setup test data
        cls.supplier = Supplier(name="Material Supplier", contact_email="materials@example.com")
        cls.session.add(cls.supplier)
        cls.session.commit()

        cls.leather = Leather(
            name="Test Leather",
            leather_type=LeatherType.VEGETABLE_TANNED,
            supplier_id=cls.supplier.id
        )

        cls.hardware = Hardware(
            name="Test Hardware",
            hardware_type=HardwareType.BUCKLE,
            supplier_id=cls.supplier.id
        )

        cls.session.add_all([cls.leather, cls.hardware])
        cls.session.commit()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_material_supplier_relationship(self):
        """Test the relationship between Material and Supplier."""
        # Retrieve from database
        leather = self.session.query(Leather).filter_by(id=self.leather.id).first()

        # Check supplier relationship
        self.assertIsNotNone(leather.supplier)
        self.assertEqual(leather.supplier.id, self.supplier.id)
        self.assertEqual(leather.supplier.name, "Material Supplier")

        # Check the reverse relationship (from supplier to materials)
        supplier = self.session.query(Supplier).filter_by(id=self.supplier.id).first()
        self.assertEqual(len(supplier.materials), 2)  # leather and hardware
        material_names = [m.name for m in supplier.materials]
        self.assertIn("Test Leather", material_names)
        self.assertIn("Test Hardware", material_names)

    def test_material_component_relationship(self):
        """Test the relationship between Material and Component through ComponentMaterial."""
        # Create a component
        component = Component(
            name="Wallet Front",
            component_type=ComponentType.LEATHER,
        )
        self.session.add(component)
        self.session.commit()

        # Create component material relationships
        comp_material1 = ComponentMaterial(
            component_id=component.id,
            material_id=self.leather.id,
            quantity=1.0
        )

        comp_material2 = ComponentMaterial(
            component_id=component.id,
            material_id=self.hardware.id,
            quantity=2.0
        )

        self.session.add_all([comp_material1, comp_material2])
        self.session.commit()

        # Test component to materials relationship
        component = self.session.query(Component).filter_by(id=component.id).first()
        self.assertEqual(len(component.component_materials), 2)
        self.assertEqual(len(component.materials), 2)

        # Test material to components relationship
        leather = self.session.query(Leather).filter_by(id=self.leather.id).first()
        self.assertEqual(len(leather.component_materials), 1)
        self.assertEqual(leather.component_materials[0].component.name, "Wallet Front")

# Additional test classes for other relationships would follow...
# (Truncated for brevity)