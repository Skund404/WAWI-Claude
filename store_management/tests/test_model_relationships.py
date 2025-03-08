# tests/test_model_relationships.py
"""
Tests specifically focusing on model relationships according to the ER diagram.
These tests ensure relationships between different entities are correctly implemented.
"""

import pytest
import datetime
from typing import Dict, Any

from database.models import (
    Customer, Sales, SalesItem, Product, ProductPattern, Pattern,
    Project, Component, ProjectComponent, PickingList, PickingListItem,
    ToolList, ToolListItem, Tool, Material, Leather, Hardware,
    ComponentMaterial, ComponentLeather, ComponentHardware, ComponentTool,
    Supplier, Purchase, PurchaseItem, ProductInventory, MaterialInventory,
    LeatherInventory, HardwareInventory, ToolInventory, Storage
)
from database.models.enums import (
    SaleStatus, PaymentStatus, ProjectStatus, ProjectType, SkillLevel,
    ComponentType, MaterialType, LeatherType, HardwareType, InventoryStatus,
    MeasurementUnit, QualityGrade
)


class TestCustomerSalesRelationships:
    """Test relationship between Customer and Sales entities."""

    def test_customer_to_sales(self, db_session, sample_data):
        """Test Customer to Sales relationship."""
        customer_id = sample_data['customer']['id']
        sale_id = sample_data['sale']['id']

        # Add another sale for the same customer
        new_sale = Sales(
            customer_id=customer_id,
            total_amount=149.99,
            status=SaleStatus.IN_PRODUCTION,
            payment_status=PaymentStatus.PARTIALLY_PAID
        )
        db_session.add(new_sale)
        db_session.commit()

        # Query customer and check sales relationship
        customer = db_session.query(Customer).get(customer_id)

        # Check if the relationship attribute exists
        assert hasattr(customer, 'sales_records') or hasattr(customer, 'sales'), \
            "Customer should have a relationship to Sales"

        # Get sales from the appropriate attribute
        if hasattr(customer, 'sales_records'):
            sales = customer.sales_records
        else:
            sales = customer.sales

        # Verify we have two sales records
        assert len(sales) == 2, "Customer should have 2 sales records"

        # Verify sales records contain the expected IDs
        sale_ids = [s.id for s in sales]
        assert sale_id in sale_ids, "Customer's sales should include the original sale"
        assert new_sale.id in sale_ids, "Customer's sales should include the new sale"

    def test_sale_to_customer(self, db_session, sample_data):
        """Test Sales to Customer relationship."""
        customer_id = sample_data['customer']['id']
        sale_id = sample_data['sale']['id']

        # Query sale and check customer relationship
        sale = db_session.query(Sales).get(sale_id)

        # Check if the relationship attribute exists
        assert hasattr(sale, 'customer'), "Sales should have a relationship to Customer"

        # Verify customer ID
        assert sale.customer.id == customer_id, "Sale should be linked to the correct customer"


class TestProductRelationships:
    """Test relationships between Product and related entities."""

    def test_product_pattern_relationship(self, db_session, sample_data):
        """Test Product to Pattern relationship via ProductPattern."""
        product_id = sample_data['product']['id']
        pattern_id = sample_data['pattern']['id']

        # Create a ProductPattern association
        product_pattern = ProductPattern(
            product_id=product_id,
            pattern_id=pattern_id
        )
        db_session.add(product_pattern)
        db_session.commit()

        # Query Product and check Pattern relationship
        product = db_session.query(Product).get(product_id)
        pattern = db_session.query(Pattern).get(pattern_id)

        # Check if patterns can be accessed from product
        patterns_attr = None
        for attr in ['patterns', 'pattern', 'product_patterns']:
            if hasattr(product, attr):
                patterns_attr = attr
                break

        assert patterns_attr is not None, "Product should have a relationship to Pattern"

        # Check if products can be accessed from pattern
        products_attr = None
        for attr in ['products', 'product', 'product_patterns']:
            if hasattr(pattern, attr):
                products_attr = attr
                break

        assert products_attr is not None, "Pattern should have a relationship to Product"

    def test_product_inventory_relationship(self, db_session, sample_data):
        """Test Product to ProductInventory relationship."""
        product_id = sample_data['product']['id']

        # Create a storage location
        storage = Storage(
            name="Test Storage",
            location_type="SHELF",
            description="A test storage location"
        )
        db_session.add(storage)
        db_session.flush()

        # Create inventory for the product
        inventory = ProductInventory(
            product_id=product_id,
            quantity=10,
            status=InventoryStatus.IN_STOCK,
            storage_location_id=storage.id
        )
        db_session.add(inventory)
        db_session.commit()

        # Query Product and check inventory relationship
        product = db_session.query(Product).get(product_id)

        # Check if inventory can be accessed from product
        inventory_attr = None
        for attr in ['inventories', 'inventory', 'product_inventories']:
            if hasattr(product, attr):
                inventory_attr = attr
                break

        assert inventory_attr is not None, "Product should have a relationship to ProductInventory"

        # Verify inventory references correct product
        product_inventories = db_session.query(ProductInventory).filter_by(product_id=product_id).all()
        assert len(product_inventories) == 1, "Should have one inventory entry for product"
        assert product_inventories[0].product_id == product_id, "Inventory should reference correct product"


class TestComponentRelationships:
    """Test relationships between Component and related entities."""

    def test_component_material_relationship(self, db_session, sample_data):
        """Test Component to Material relationship."""
        component_id = sample_data['component']['id']
        material_id = sample_data['material']['id']

        # Create a ComponentMaterial association
        comp_material = ComponentMaterial(
            component_id=component_id,
            material_id=material_id,
            quantity=2.5
        )
        db_session.add(comp_material)
        db_session.commit()

        # Query Component and verify the material relationship
        component_materials = db_session.query(ComponentMaterial).filter_by(component_id=component_id).all()
        assert len(component_materials) == 1, "Component should have 1 material"
        assert component_materials[0].material_id == material_id, "Component material should reference correct material"
        assert component_materials[0].quantity == 2.5, "Component material should have correct quantity"

    def test_component_leather_relationship(self, db_session, sample_data):
        """Test Component to Leather relationship."""
        component_id = sample_data['component']['id']
        leather_id = sample_data['leather']['id']

        # Create a ComponentLeather association
        comp_leather = ComponentLeather(
            component_id=component_id,
            leather_id=leather_id,
            quantity=1.5
        )
        db_session.add(comp_leather)
        db_session.commit()

        # Query Component and verify the leather relationship
        component_leathers = db_session.query(ComponentLeather).filter_by(component_id=component_id).all()
        assert len(component_leathers) == 1, "Component should have 1 leather"
        assert component_leathers[0].leather_id == leather_id, "Component leather should reference correct leather"
        assert component_leathers[0].quantity == 1.5, "Component leather should have correct quantity"

    def test_component_hardware_relationship(self, db_session, sample_data):
        """Test Component to Hardware relationship."""
        component_id = sample_data['component']['id']
        hardware_id = sample_data['hardware']['id']

        # Create a ComponentHardware association
        comp_hardware = ComponentHardware(
            component_id=component_id,
            hardware_id=hardware_id,
            quantity=4
        )
        db_session.add(comp_hardware)
        db_session.commit()

        # Query Component and verify the hardware relationship
        component_hardwares = db_session.query(ComponentHardware).filter_by(component_id=component_id).all()
        assert len(component_hardwares) == 1, "Component should have 1 hardware"
        assert component_hardwares[0].hardware_id == hardware_id, "Component hardware should reference correct hardware"
        assert component_hardwares[0].quantity == 4, "Component hardware should have correct quantity"

    def test_component_tool_relationship(self, db_session, sample_data):
        """Test Component to Tool relationship."""
        component_id = sample_data['component']['id']
        tool_id = sample_data['tool']['id']

        # Create a ComponentTool association
        comp_tool = ComponentTool(
            component_id=component_id,
            tool_id=tool_id
        )
        db_session.add(comp_tool)
        db_session.commit()

        # Query Component and verify the tool relationship
        component_tools = db_session.query(ComponentTool).filter_by(component_id=component_id).all()
        assert len(component_tools) == 1, "Component should have 1 tool"
        assert component_tools[0].tool_id == tool_id, "Component tool should reference correct tool"


class TestProjectRelationships:
    """Test relationships between Project and related entities."""

    def test_project_component_relationship(self, db_session, sample_data):
        """Test Project to Component relationship via ProjectComponent."""
        # Create a project
        project = Project(
            name="Test Project",
            description="A test project",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE,
            start_date=datetime.datetime.utcnow()
        )
        db_session.add(project)
        db_session.flush()

        component_id = sample_data['component']['id']

        # Create a ProjectComponent association
        project_component = ProjectComponent(
            project_id=project.id,
            component_id=component_id,
            quantity=2
        )
        db_session.add(project_component)
        db_session.commit()

        # Query Project and check component relationship
        saved_project = db_session.query(Project).get(project.id)

        # Check if components can be accessed from project
        components_attr = None
        for attr in ['components', 'project_components']:
            if hasattr(saved_project, attr):
                components_attr = attr
                break

        assert components_attr is not None, "Project should have a relationship to components"

        # Query components directly using the join table
        project_components = db_session.query(ProjectComponent).filter_by(project_id=project.id).all()
        assert len(project_components) == 1, "Project should have 1 component"
        assert project_components[0].component_id == component_id, "ProjectComponent should reference correct component"
        assert project_components[0].quantity == 2, "ProjectComponent should have correct quantity"

    def test_project_toollist_relationship(self, db_session, sample_data):
        """Test Project to ToolList relationship."""
        # Create a project
        project = Project(
            name="Tool Project",
            description="A project with tools",
            type=ProjectType.WALLET,
            status=ProjectStatus.DESIGN_PHASE,
            start_date=datetime.datetime.utcnow()
        )
        db_session.add(project)
        db_session.flush()

        # Create a ToolList for the project
        tool_list = ToolList(
            project_id=project.id,
            status="pending"
        )
        db_session.add(tool_list)
        db_session.flush()

        # Add a tool to the list
        tool_id = sample_data['tool']['id']
        list_item = ToolListItem(
            tool_list_id=tool_list.id,
            tool_id=tool_id,
            quantity=1
        )
        db_session.add(list_item)
        db_session.commit()

        # Query Project and check ToolList relationship
        saved_project = db_session.query(Project).get(project.id)

        # Check if tool_list can be accessed from project
        tool_list_attr = None
        for attr in ['tool_list', 'tool_lists']:
            if hasattr(saved_project, attr):
                tool_list_attr = attr
                break

        assert tool_list_attr is not None, "Project should have a relationship to ToolList"

        # Query ToolList directly
        saved_tool_list = db_session.query(ToolList).filter_by(project_id=project.id).first()
        assert saved_tool_list is not None, "Should be able to query ToolList for project"
        assert saved_tool_list.project_id == project.id, "ToolList should reference correct project"

        # Check if we can access tool items
        tool_items_attr = None
        for attr in ['items', 'tools', 'tool_list_items']:
            if hasattr(saved_tool_list, attr):
                tool_items_attr = attr
                break

        assert tool_items_attr is not None, "ToolList should have a relationship to ToolListItem"

        # Query ToolListItem directly
        list_items = db_session.query(ToolListItem).filter_by(tool_list_id=tool_list.id).all()
        assert len(list_items) == 1, "ToolList should have 1 tool"
        assert list_items[0].tool_id == tool_id, "ToolListItem should reference correct tool"


class TestPickingListRelationships:
    """Test relationships between PickingList and related entities."""

    def test_pickinglist_items_relationship(self, db_session, sample_data):
        """Test PickingList to PickingListItem relationship."""
        # Create a picking list
        sale_id = sample_data['sale']['id']
        picking_list = PickingList(
            sales_id=sale_id,
            status="pending"
        )
        db_session.add(picking_list)
        db_session.flush()

        # Add items to the picking list
        material_id = sample_data['material']['id']
        leather_id = sample_data['leather']['id']

        # Material item
        material_item = PickingListItem(
            picking_list_id=picking_list.id,
            material_id=material_id,
            quantity_ordered=5,
            quantity_picked=3
        )

        # Leather item
        leather_item = PickingListItem(
            picking_list_id=picking_list.id,
            leather_id=leather_id,
            quantity_ordered=2,
            quantity_picked=1
        )

        db_session.add_all([material_item, leather_item])
        db_session.commit()

        # Query PickingList and check items relationship
        saved_picking_list = db_session.query(PickingList).get(picking_list.id)

        # Check if items can be accessed from picking list
        items_attr = None
        for attr in ['items', 'picking_list_items']:
            if hasattr(saved_picking_list, attr):
                items_attr = attr
                break

        assert items_attr is not None, "PickingList should have a relationship to items"

        # Query items directly
        list_items = db_session.query(PickingListItem).filter_by(picking_list_id=picking_list.id).all()
        assert len(list_items) == 2, "PickingList should have 2 items"

        # Verify material item
        material_items = [i for i in list_items if i.material_id == material_id]
        assert len(material_items) == 1, "Should have 1 material item"
        assert material_items[0].quantity_ordered == 5, "Material item should have correct quantity ordered"
        assert material_items[0].quantity_picked == 3, "Material item should have correct quantity picked"

        # Verify leather item
        leather_items = [i for i in list_items if i.leather_id == leather_id]
        assert len(leather_items) == 1, "Should have 1 leather item"
        assert leather_items[0].quantity_ordered == 2, "Leather item should have correct quantity ordered"
        assert leather_items[0].quantity_picked == 1, "Leather item should have correct quantity picked"


class TestSupplierRelationships:
    """Test relationships between Supplier and related entities."""

    def test_supplier_materials_relationship(self, db_session, sample_data):
        """Test Supplier to Material relationship."""
        supplier_id = sample_data['supplier']['id']

        # Query supplier and check material relationship
        supplier = db_session.query(Supplier).get(supplier_id)

        # Check materials attribute
        materials_attr = None
        for attr in ['materials', 'material']:
            if hasattr(supplier, attr):
                materials_attr = attr
                break

        assert materials_attr is not None, "Supplier should have a relationship to Materials"

        # Query materials directly
        materials = db_session.query(Material).filter_by(supplier_id=supplier_id).all()
        assert len(materials) > 0, "Supplier should have associated materials"

    def test_supplier_purchases_relationship(self, db_session, sample_data):
        """Test Supplier to Purchase relationship."""
        supplier_id = sample_data['supplier']['id']

        # Create a purchase
        purchase = Purchase(
            supplier_id=supplier_id,
            total_amount=499.99,
            status="PENDING"
        )
        db_session.add(purchase)
        db_session.flush()

        # Add purchase items
        material_id = sample_data['material']['id']
        purchase_item = PurchaseItem(
            purchase_id=purchase.id,
            material_id=material_id,
            quantity=10,
            price=49.99
        )
        db_session.add(purchase_item)
        db_session.commit()

        # Query supplier and check purchase relationship
        supplier = db_session.query(Supplier).get(supplier_id)

        # Check purchases attribute
        purchases_attr = None
        for attr in ['purchases', 'purchase']:
            if hasattr(supplier, attr):
                purchases_attr = attr
                break

        assert purchases_attr is not None, "Supplier should have a relationship to Purchases"

        # Query purchases directly
        purchases = db_session.query(Purchase).filter_by(supplier_id=supplier_id).all()
        assert len(purchases) == 1, "Supplier should have 1 purchase"
        assert purchases[0].total_amount == 499.99, "Purchase should have correct amount"

        # Check purchase items
        purchase_items = db_session.query(PurchaseItem).filter_by(purchase_id=purchase.id).all()
        assert len(purchase_items) == 1, "Purchase should have 1 item"
        assert purchase_items[0].material_id == material_id, "Purchase item should reference correct material"


class TestInventoryRelationships:
    """Test relationships between inventory entities and their base entities."""

    def test_material_inventory_relationship(self, db_session, sample_data):
        """Test Material to MaterialInventory relationship."""
        material_id = sample_data['material']['id']

        # Create a storage location
        storage = Storage(
            name="Material Storage",
            location_type="BIN",
            description="Storage for materials"
        )
        db_session.add(storage)
        db_session.flush()

        # Create inventory record
        inventory = MaterialInventory(
            material_id=material_id,
            quantity=15.5,
            status=InventoryStatus.IN_STOCK,
            storage_location_id=storage.id
        )
        db_session.add(inventory)
        db_session.commit()

        # Query Material and check inventory relationship
        material = db_session.query(Material).get(material_id)

        # Check inventory attribute
        inventory_attr = None
        for attr in ['inventories', 'inventory', 'material_inventories']:
            if hasattr(material, attr):
                inventory_attr = attr
                break

        assert inventory_attr is not None, "Material should have a relationship to MaterialInventory"

        # Query inventory directly
        inventories = db_session.query(MaterialInventory).filter_by(material_id=material_id).all()
        assert len(inventories) == 1, "Material should have 1 inventory record"
        assert inventories[0].quantity == 15.5, "Inventory should have correct quantity"
        assert inventories[0].status == InventoryStatus.IN_STOCK, "Inventory should have correct status"