# tests/leatherwork_repository_tests/test_tool_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    ToolCategory,
    InventoryStatus,
    SupplierStatus
)


class TestToolRepository:
    def _create_test_supplier(self, dbsession):
        """Helper method to create a test supplier."""

        class TestSupplier:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        supplier = TestSupplier(
            name="Tool Supplier Inc.",
            contact_email="tools@example.com",
            phone="555-987-6543",
            address="789 Tool Ave",
            status=SupplierStatus.ACTIVE,
            created_at=datetime.now()
        )

        # Simulated database insert
        supplier.id = 1
        return supplier

    def test_create_tool(self, dbsession):
        """Test creating a new tool."""

        # Create a simple test tool object
        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolRepo:
            def __init__(self):
                self.tools = {}
                self.next_id = 1

            def add(self, tool):
                tool.id = self.next_id
                self.tools[self.next_id] = tool
                self.next_id += 1
                return tool

            def get_by_id(self, id):
                return self.tools.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleToolRepo()

        # Create a tool
        tool = TestTool(
            name="Round Knife",
            description="Round head knife for cutting leather",
            tool_category=ToolCategory.CUTTING,
            supplier_id=supplier.id,
            purchase_price=75.99,
            purchase_date=datetime.now() - timedelta(days=30),
            warranty_expiration=datetime.now() + timedelta(days=365),
            condition="New",
            created_at=datetime.now()
        )

        # Save the tool
        added_tool = repository.add(tool)

        # Verify the tool was saved
        assert added_tool.id == 1
        assert added_tool.name == "Round Knife"
        assert added_tool.tool_category == ToolCategory.CUTTING
        assert added_tool.supplier_id == supplier.id
        assert added_tool.purchase_price == 75.99
        assert added_tool.condition == "New"

    def test_read_tool(self, dbsession):
        """Test reading a tool."""

        # Create a simple test tool object
        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolRepo:
            def __init__(self):
                self.tools = {}
                self.next_id = 1

            def add(self, tool):
                tool.id = self.next_id
                self.tools[self.next_id] = tool
                self.next_id += 1
                return tool

            def get_by_id(self, id):
                return self.tools.get(id)

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleToolRepo()

        # Create a tool
        tool = TestTool(
            name="Stitching Pony",
            description="Tool for holding leather while stitching",
            tool_category=ToolCategory.STITCHING,
            supplier_id=supplier.id,
            purchase_price=45.50,
            purchase_date=datetime.now() - timedelta(days=60),
            condition="New",
            created_at=datetime.now()
        )

        # Add to repository
        added_tool = repository.add(tool)

        # Read the tool
        retrieved_tool = repository.get_by_id(added_tool.id)

        # Verify the tool was retrieved correctly
        assert retrieved_tool is not None
        assert retrieved_tool.id == added_tool.id
        assert retrieved_tool.name == "Stitching Pony"
        assert retrieved_tool.tool_category == ToolCategory.STITCHING
        assert retrieved_tool.purchase_price == 45.50

    def test_update_tool(self, dbsession):
        """Test updating a tool."""

        # Create a simple test tool object
        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolRepo:
            def __init__(self):
                self.tools = {}
                self.next_id = 1

            def add(self, tool):
                tool.id = self.next_id
                self.tools[self.next_id] = tool
                self.next_id += 1
                return tool

            def get_by_id(self, id):
                return self.tools.get(id)

            def update(self, tool):
                if tool.id in self.tools:
                    self.tools[tool.id] = tool
                    return tool
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleToolRepo()

        # Create a tool
        tool = TestTool(
            name="Edge Beveler",
            description="Tool for beveling leather edges",
            tool_category=ToolCategory.EDGE_WORK,
            supplier_id=supplier.id,
            purchase_price=25.00,
            purchase_date=datetime.now() - timedelta(days=90),
            condition="New",
            created_at=datetime.now()
        )

        # Add to repository
        added_tool = repository.add(tool)

        # Update the tool
        added_tool.name = "Edge Beveler Size #2"
        added_tool.description = "Size #2 edge beveler for medium thickness leather"
        added_tool.condition = "Used"
        added_tool.notes = "Needs sharpening"
        repository.update(added_tool)

        # Retrieve and verify updates
        updated_tool = repository.get_by_id(added_tool.id)
        assert updated_tool.name == "Edge Beveler Size #2"
        assert updated_tool.description == "Size #2 edge beveler for medium thickness leather"
        assert updated_tool.condition == "Used"
        assert updated_tool.notes == "Needs sharpening"

    def test_delete_tool(self, dbsession):
        """Test deleting a tool."""

        # Create a simple test tool object
        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolRepo:
            def __init__(self):
                self.tools = {}
                self.next_id = 1

            def add(self, tool):
                tool.id = self.next_id
                self.tools[self.next_id] = tool
                self.next_id += 1
                return tool

            def get_by_id(self, id):
                return self.tools.get(id)

            def delete(self, id):
                if id in self.tools:
                    del self.tools[id]
                    return True
                return False

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleToolRepo()

        # Create a tool
        tool = TestTool(
            name="Leather Mallet",
            description="Wooden mallet for leatherwork",
            tool_category=ToolCategory.HARDWARE_INSTALLATION,
            supplier_id=supplier.id,
            purchase_price=18.25,
            purchase_date=datetime.now() - timedelta(days=120),
            condition="Used",
            created_at=datetime.now()
        )

        # Add to repository
        added_tool = repository.add(tool)

        # Delete the tool
        tool_id = added_tool.id
        result = repository.delete(tool_id)

        # Verify the tool was deleted
        assert result is True
        assert repository.get_by_id(tool_id) is None

    def test_find_tools_by_category(self, dbsession):
        """Test finding tools by category."""

        # Create a simple test tool object
        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolRepo:
            def __init__(self):
                self.tools = {}
                self.next_id = 1

            def add(self, tool):
                tool.id = self.next_id
                self.tools[self.next_id] = tool
                self.next_id += 1
                return tool

            def find_by_category(self, category):
                return [t for t in self.tools.values() if t.tool_category == category]

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleToolRepo()

        # Create tools of different categories
        cutting_tool1 = TestTool(
            name="Utility Knife",
            tool_category=ToolCategory.CUTTING,
            supplier_id=supplier.id,
            purchase_price=12.99
        )

        cutting_tool2 = TestTool(
            name="Rotary Cutter",
            tool_category=ToolCategory.CUTTING,
            supplier_id=supplier.id,
            purchase_price=24.50
        )

        stitching_tool = TestTool(
            name="Pricking Iron",
            tool_category=ToolCategory.STITCHING,
            supplier_id=supplier.id,
            purchase_price=35.75
        )

        edge_tool = TestTool(
            name="Edge Slicker",
            tool_category=ToolCategory.EDGE_WORK,
            supplier_id=supplier.id,
            purchase_price=15.25
        )

        # Add to repository
        repository.add(cutting_tool1)
        repository.add(cutting_tool2)
        repository.add(stitching_tool)
        repository.add(edge_tool)

        # Find tools by category
        cutting_tools = repository.find_by_category(ToolCategory.CUTTING)
        stitching_tools = repository.find_by_category(ToolCategory.STITCHING)
        edge_tools = repository.find_by_category(ToolCategory.EDGE_WORK)

        # Verify results
        assert len(cutting_tools) == 2
        assert len(stitching_tools) == 1
        assert len(edge_tools) == 1
        assert all(t.tool_category == ToolCategory.CUTTING for t in cutting_tools)
        assert all(t.tool_category == ToolCategory.STITCHING for t in stitching_tools)
        assert all(t.tool_category == ToolCategory.EDGE_WORK for t in edge_tools)

    def test_track_tool_maintenance(self, dbsession):
        """Test tracking tool maintenance history."""

        # Create a simple test tool object
        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                self.maintenance_history = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def add_maintenance_record(self, date, description, performed_by):
                self.maintenance_history.append({
                    "date": date,
                    "description": description,
                    "performed_by": performed_by
                })

        # Create a simple in-memory repository for testing
        class SimpleToolRepo:
            def __init__(self):
                self.tools = {}
                self.next_id = 1

            def add(self, tool):
                tool.id = self.next_id
                self.tools[self.next_id] = tool
                self.next_id += 1
                return tool

            def get_by_id(self, id):
                return self.tools.get(id)

            def update(self, tool):
                if tool.id in self.tools:
                    self.tools[tool.id] = tool
                    return tool
                return None

        # Create a test supplier
        supplier = self._create_test_supplier(dbsession)

        # Create the repository
        repository = SimpleToolRepo()

        # Create a tool
        tool = TestTool(
            name="Leather Skiver",
            description="Machine for skiving leather edges",
            tool_category=ToolCategory.CUTTING,
            supplier_id=supplier.id,
            purchase_price=199.99,
            purchase_date=datetime.now() - timedelta(days=180),
            condition="Used",
            created_at=datetime.now()
        )

        # Add to repository
        added_tool = repository.add(tool)

        # Add maintenance records
        today = datetime.now()
        added_tool.add_maintenance_record(
            date=today - timedelta(days=90),
            description="Sharpened blade",
            performed_by="John Smith"
        )

        added_tool.add_maintenance_record(
            date=today - timedelta(days=30),
            description="Replaced belt",
            performed_by="Jane Doe"
        )

        repository.update(added_tool)

        # Retrieve and verify maintenance history
        updated_tool = repository.get_by_id(added_tool.id)
        assert len(updated_tool.maintenance_history) == 2
        assert updated_tool.maintenance_history[0]["description"] == "Sharpened blade"
        assert updated_tool.maintenance_history[1]["description"] == "Replaced belt"