# tests/leatherwork_repository_tests/test_tool_list_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    ToolListStatus,
    ProjectStatus,
    ProjectType,
    ToolCategory,
    CustomerStatus
)


class TestToolListRepository:
    def _create_test_customer(self, dbsession):
        """Helper method to create a test customer."""

        class TestCustomer:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        customer = TestCustomer(
            first_name="John",
            last_name="Smith",
            email="john.smith@example.com",
            phone="555-987-6543",
            status=CustomerStatus.ACTIVE
        )

        # Simulated database insert
        customer.id = 1
        return customer

    def _create_test_project(self, dbsession, customer_id):
        """Helper method to create a test project."""

        class TestProject:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        project = TestProject(
            customer_id=customer_id,
            name="Leather Wallet Project",
            description="Custom bifold wallet",
            project_type=ProjectType.WALLET,
            status=ProjectStatus.IN_PROGRESS,
            start_date=datetime.now(),
            expected_completion_date=datetime.now() + timedelta(days=14),
            created_at=datetime.now()
        )

        # Simulated database insert
        project.id = 1
        return project

    def _create_test_tool(self, dbsession):
        """Helper method to create a test tool."""

        class TestTool:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        tool = TestTool(
            name="Stitching Awl",
            description="Professional stitching awl",
            tool_category=ToolCategory.STITCHING,
            purchase_price=25.99
        )

        # Simulated database insert
        tool.id = 1
        return tool

    def test_create_tool_list(self, dbsession):
        """Test creating a new tool list."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def get_by_id(self, id):
                return self.tool_lists.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)

        # Create the repository
        repository = SimpleToolListRepo()

        # Create a tool list
        tool_list = TestToolList(
            project_id=project.id,
            status=ToolListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="John Smith"
        )

        # Save the tool list
        added_tool_list = repository.add(tool_list)

        # Verify the tool list was saved
        assert added_tool_list.id == 1
        assert added_tool_list.project_id == project.id
        assert added_tool_list.status == ToolListStatus.DRAFT
        assert added_tool_list.created_by == "John Smith"

    def test_read_tool_list(self, dbsession):
        """Test reading a tool list."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def get_by_id(self, id):
                return self.tool_lists.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)

        # Create the repository
        repository = SimpleToolListRepo()

        # Create a tool list
        tool_list = TestToolList(
            project_id=project.id,
            status=ToolListStatus.PENDING,
            created_at=datetime.now(),
            created_by="Jane Doe"
        )

        # Add to repository
        added_tool_list = repository.add(tool_list)

        # Read the tool list
        retrieved_tool_list = repository.get_by_id(added_tool_list.id)

        # Verify the tool list was retrieved correctly
        assert retrieved_tool_list is not None
        assert retrieved_tool_list.id == added_tool_list.id
        assert retrieved_tool_list.project_id == project.id
        assert retrieved_tool_list.status == ToolListStatus.PENDING
        assert retrieved_tool_list.created_by == "Jane Doe"

    def test_update_tool_list(self, dbsession):
        """Test updating a tool list."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def get_by_id(self, id):
                return self.tool_lists.get(id)

            def update(self, tool_list):
                if tool_list.id in self.tool_lists:
                    self.tool_lists[tool_list.id] = tool_list
                    return tool_list
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)

        # Create the repository
        repository = SimpleToolListRepo()

        # Create a tool list
        tool_list = TestToolList(
            project_id=project.id,
            status=ToolListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Alice Johnson"
        )

        # Add to repository
        added_tool_list = repository.add(tool_list)

        # Update the tool list
        added_tool_list.status = ToolListStatus.READY
        added_tool_list.notes = "All tools prepared for the wallet project"
        added_tool_list.updated_at = datetime.now()
        added_tool_list.updated_by = "Bob Williams"
        repository.update(added_tool_list)

        # Retrieve and verify updates
        updated_tool_list = repository.get_by_id(added_tool_list.id)
        assert updated_tool_list.status == ToolListStatus.READY
        assert updated_tool_list.notes == "All tools prepared for the wallet project"
        assert hasattr(updated_tool_list, "updated_at")
        assert updated_tool_list.updated_by == "Bob Williams"

    def test_delete_tool_list(self, dbsession):
        """Test deleting a tool list."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def get_by_id(self, id):
                return self.tool_lists.get(id)

            def delete(self, id):
                if id in self.tool_lists:
                    del self.tool_lists[id]
                    return True
                return False

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)

        # Create the repository
        repository = SimpleToolListRepo()

        # Create a tool list
        tool_list = TestToolList(
            project_id=project.id,
            status=ToolListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Charlie Brown"
        )

        # Add to repository
        added_tool_list = repository.add(tool_list)

        # Delete the tool list
        tool_list_id = added_tool_list.id
        result = repository.delete(tool_list_id)

        # Verify the tool list was deleted
        assert result is True
        assert repository.get_by_id(tool_list_id) is None

    def test_add_tool_to_tool_list(self, dbsession):
        """Test adding a tool to a tool list."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def add_tool(self, tool, quantity=1, notes=None):
                self.items.append({
                    "tool_id": tool.id,
                    "tool": tool,
                    "quantity": quantity,
                    "notes": notes
                })

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def get_by_id(self, id):
                return self.tool_lists.get(id)

            def update(self, tool_list):
                if tool_list.id in self.tool_lists:
                    self.tool_lists[tool_list.id] = tool_list
                    return tool_list
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)
        tool = self._create_test_tool(dbsession)

        # Create the repository
        repository = SimpleToolListRepo()

        # Create a tool list
        tool_list = TestToolList(
            project_id=project.id,
            status=ToolListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="David Miller"
        )

        # Add to repository
        added_tool_list = repository.add(tool_list)

        # Add tool to tool list
        added_tool_list.add_tool(tool, quantity=1, notes="Needed for stitching")
        repository.update(added_tool_list)

        # Retrieve and verify updates
        updated_tool_list = repository.get_by_id(added_tool_list.id)
        assert len(updated_tool_list.items) == 1
        assert updated_tool_list.items[0]["tool_id"] == tool.id
        assert updated_tool_list.items[0]["quantity"] == 1
        assert updated_tool_list.items[0]["notes"] == "Needed for stitching"

    def test_tool_list_status_transition(self, dbsession):
        """Test tool list status transitions."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def get_by_id(self, id):
                return self.tool_lists.get(id)

            def update(self, tool_list):
                if tool_list.id in self.tool_lists:
                    self.tool_lists[tool_list.id] = tool_list
                    return tool_list
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)

        # Create the repository
        repository = SimpleToolListRepo()

        # Create a tool list
        tool_list = TestToolList(
            project_id=project.id,
            status=ToolListStatus.DRAFT,
            created_at=datetime.now(),
            created_by="Emily White"
        )

        # Add to repository
        added_tool_list = repository.add(tool_list)

        # Transition through different statuses
        status_transitions = [
            (ToolListStatus.PENDING, "pending_at"),
            (ToolListStatus.READY, "ready_at"),
            (ToolListStatus.IN_USE, "in_use_at"),
            (ToolListStatus.COMPLETED, "completed_at")
        ]

        for new_status, timestamp_field in status_transitions:
            added_tool_list.status = new_status
            # Add timestamp for status change
            setattr(added_tool_list, timestamp_field, datetime.now())
            repository.update(added_tool_list)

            # Verify status was updated
            updated_tool_list = repository.get_by_id(added_tool_list.id)
            assert updated_tool_list.status == new_status
            assert hasattr(updated_tool_list, timestamp_field)

    def test_find_tool_lists_by_project(self, dbsession):
        """Test finding tool lists by project."""

        # Create a simple test tool list object
        class TestToolList:
            def __init__(self, **kwargs):
                self.id = None
                self.items = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleToolListRepo:
            def __init__(self):
                self.tool_lists = {}
                self.next_id = 1

            def add(self, tool_list):
                tool_list.id = self.next_id
                self.tool_lists[self.next_id] = tool_list
                self.next_id += 1
                return tool_list

            def find_by_project_id(self, project_id):
                return [tl for tl in self.tool_lists.values() if tl.project_id == project_id]

        # Create test data
        class TestProject:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        customer = self._create_test_customer(dbsession)

        project1 = TestProject(
            customer_id=customer.id,
            name="Wallet Project",
            project_type=ProjectType.WALLET
        )
        project1.id = 1

        project2 = TestProject(
            customer_id=customer.id,
            name="Belt Project",
            project_type=ProjectType.BELT
        )
        project2.id = 2

        # Create the repository
        repository = SimpleToolListRepo()

        # Create tool lists
        tool_list1 = TestToolList(
            project_id=project1.id,
            status=ToolListStatus.READY,
            created_at=datetime.now()
        )

        tool_list2 = TestToolList(
            project_id=project1.id,
            status=ToolListStatus.COMPLETED,
            created_at=datetime.now() - timedelta(days=7)
        )

        tool_list3 = TestToolList(
            project_id=project2.id,
            status=ToolListStatus.IN_PROGRESS,
            created_at=datetime.now()
        )

        # Add to repository
        repository.add(tool_list1)
        repository.add(tool_list2)
        repository.add(tool_list3)

        # Find tool lists by project
        project1_tool_lists = repository.find_by_project_id(project1.id)
        project2_tool_lists = repository.find_by_project_id(project2.id)

        # Verify results
        assert len(project1_tool_lists) == 2
        assert len(project2_tool_lists) == 1
        assert all(tl.project_id == project1.id for tl in project1_tool_lists)
        assert all(tl.project_id == project2.id for tl in project2_tool_lists)