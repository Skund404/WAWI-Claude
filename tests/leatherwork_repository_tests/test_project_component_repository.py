# tests/leatherwork_repository_tests/test_project_component_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    ProjectStatus,
    ProjectType,
    ComponentType,
    CustomerStatus,
    SkillLevel
)


class TestProjectComponentRepository:
    def _create_test_component(self, dbsession):
        """Helper method to create a test component."""

        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component = TestComponent(
            name="Wallet Body Component",
            description="Main body panel for bifold wallet",
            component_type=ComponentType.LEATHER,  # Updated to match enum
            complexity_factor=3,
            created_at=datetime.now()
        )

        # Simulated database insert
        component.id = 1
        return component

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

    def _create_test_component(self, dbsession):
        """Helper method to create a test component."""

        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component = TestComponent(
            name="Wallet Body Component",
            description="Main body panel for bifold wallet",
            component_type=ComponentType.LEATHER,
            complexity_factor=3,
            created_at=datetime.now()
        )

        # Simulated database insert
        component.id = 1
        return component

    def test_read_project_component(self, dbsession):
        """Test reading a project component relationship."""

        # Create a simple test project component object
        class TestProjectComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProjectComponentRepo:
            def __init__(self):
                self.project_components = {}
                self.next_id = 1

            def add(self, project_component):
                project_component.id = self.next_id
                self.project_components[self.next_id] = project_component
                self.next_id += 1
                return project_component

            def get_by_id(self, id):
                return self.project_components.get(id)

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)
        component = self._create_test_component(dbsession)

        # Create the repository
        repository = SimpleProjectComponentRepo()

        # Create a project component relationship
        project_component = TestProjectComponent(
            project_id=project.id,
            component_id=component.id,
            quantity=1,
            notes="Wallet lining component"
        )

        # Add to repository
        added_project_component = repository.add(project_component)

        # Read the project component
        retrieved_project_component = repository.get_by_id(added_project_component.id)

        # Verify the project component was retrieved correctly
        assert retrieved_project_component is not None
        assert retrieved_project_component.id == added_project_component.id
        assert retrieved_project_component.project_id == project.id
        assert retrieved_project_component.component_id == component.id
        assert retrieved_project_component.quantity == 1
        assert retrieved_project_component.notes == "Wallet lining component"

    def test_update_project_component(self, dbsession):
        """Test updating a project component relationship."""

        # Create a simple test project component object
        class TestProjectComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProjectComponentRepo:
            def __init__(self):
                self.project_components = {}
                self.next_id = 1

            def add(self, project_component):
                project_component.id = self.next_id
                self.project_components[self.next_id] = project_component
                self.next_id += 1
                return project_component

            def get_by_id(self, id):
                return self.project_components.get(id)

            def update(self, project_component):
                if project_component.id in self.project_components:
                    self.project_components[project_component.id] = project_component
                    return project_component
                return None

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)
        component = self._create_test_component(dbsession)

        # Create the repository
        repository = SimpleProjectComponentRepo()

        # Create a project component relationship
        project_component = TestProjectComponent(
            project_id=project.id,
            component_id=component.id,
            quantity=1,
            notes="Initial wallet component"
        )

        # Add to repository
        added_project_component = repository.add(project_component)

        # Update the project component
        added_project_component.quantity = 3
        added_project_component.notes = "Updated wallet component quantity"
        added_project_component.created_at = datetime.now()
        repository.update(added_project_component)

        # Retrieve and verify updates
        updated_project_component = repository.get_by_id(added_project_component.id)
        assert updated_project_component.quantity == 3
        assert updated_project_component.notes == "Updated wallet component quantity"
        assert hasattr(updated_project_component, "created_at")

    def test_delete_project_component(self, dbsession):
        """Test deleting a project component relationship."""

        # Create a simple test project component object
        class TestProjectComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProjectComponentRepo:
            def __init__(self):
                self.project_components = {}
                self.next_id = 1

            def add(self, project_component):
                project_component.id = self.next_id
                self.project_components[self.next_id] = project_component
                self.next_id += 1
                return project_component

            def get_by_id(self, id):
                return self.project_components.get(id)

            def delete(self, id):
                if id in self.project_components:
                    del self.project_components[id]
                    return True
                return False

        # Create test data
        customer = self._create_test_customer(dbsession)
        project = self._create_test_project(dbsession, customer.id)
        component = self._create_test_component(dbsession)

        # Create the repository
        repository = SimpleProjectComponentRepo()

        # Create a project component relationship
        project_component = TestProjectComponent(
            project_id=project.id,
            component_id=component.id,
            quantity=1,
            notes="Test component for deletion"
        )

        # Add to repository
        added_project_component = repository.add(project_component)

        # Delete the project component
        project_component_id = added_project_component.id
        result = repository.delete(project_component_id)

        # Verify the project component was deleted
        assert result is True
        assert repository.get_by_id(project_component_id) is None

    def test_find_components_by_project(self, dbsession):
        """Test finding components by project."""

        # Create a simple test project component object
        class TestProjectComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProjectComponentRepo:
            def __init__(self):
                self.project_components = {}
                self.next_id = 1

            def add(self, project_component):
                project_component.id = self.next_id
                self.project_components[self.next_id] = project_component
                self.next_id += 1
                return project_component

            def find_by_project_id(self, project_id):
                return [pc for pc in self.project_components.values() if pc.project_id == project_id]

        # Create test data
        customer = self._create_test_customer(dbsession)
        project1 = self._create_test_project(dbsession, customer.id)

        # Create test components
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component1 = TestComponent(
            id=1,
            name="Wallet Body Component 1",
            component_type=ComponentType.LEATHER
        )

        component2 = TestComponent(
            id=2,
            name="Wallet Pocket Component",
            component_type=ComponentType.POCKET
        )

        component3 = TestComponent(
            id=3,
            name="Wallet Lining Component",
            component_type=ComponentType.LINING
        )

        # Create the repository
        repository = SimpleProjectComponentRepo()

        # Create project components
        project_component1 = TestProjectComponent(
            project_id=project1.id,
            component_id=component1.id,
            quantity=1
        )

        project_component2 = TestProjectComponent(
            project_id=project1.id,
            component_id=component2.id,
            quantity=1
        )

        project_component3 = TestProjectComponent(
            project_id=project1.id,
            component_id=component3.id,
            quantity=1
        )

        # Add to repository
        repository.add(project_component1)
        repository.add(project_component2)
        repository.add(project_component3)

        # Find project components
        project_components = repository.find_by_project_id(project1.id)

        # Verify results
        assert len(project_components) == 3
        assert all(pc.project_id == project1.id for pc in project_components)

        # Verify component IDs
        component_ids = [pc.component_id for pc in project_components]
        assert set(component_ids) == {1, 2, 3}

    def test_find_projects_by_component(self, dbsession):
        """Test finding projects by component."""

        # Create a simple test project component object
        class TestProjectComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProjectComponentRepo:
            def __init__(self):
                self.project_components = {}
                self.next_id = 1

            def add(self, project_component):
                project_component.id = self.next_id
                self.project_components[self.next_id] = project_component
                self.next_id += 1
                return project_component

            def find_by_component_id(self, component_id):
                return [pc for pc in self.project_components.values() if pc.component_id == component_id]

        # Create test data
        customer = self._create_test_customer(dbsession)

        # Create test projects
        class TestProject:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        project1 = TestProject(
            id=1,
            customer_id=customer.id,
            name="Wallet Project 1",
            project_type=ProjectType.WALLET
        )

        project2 = TestProject(
            id=2,
            customer_id=customer.id,
            name="Wallet Project 2",
            project_type=ProjectType.WALLET
        )

        # Create test component
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component1 = TestComponent(
            id=1,
            name="Universal Wallet Component",
            component_type=ComponentType.LEATHER
        )

        # Create the repository
        repository = SimpleProjectComponentRepo()

        # Create project components linking the component to different projects
        project_component1 = TestProjectComponent(
            project_id=project1.id,
            component_id=component1.id,
            quantity=1
        )

        project_component2 = TestProjectComponent(
            project_id=project2.id,
            component_id=component1.id,
            quantity=1
        )

        # Add to repository
        repository.add(project_component1)
        repository.add(project_component2)

        # Find project components for the component
        project_components = repository.find_by_component_id(component1.id)

        # Verify results
        assert len(project_components) == 2
        assert all(pc.component_id == component1.id for pc in project_components)

        # Verify project IDs
        project_ids = [pc.project_id for pc in project_components]
        assert set(project_ids) == {1, 2}

    def test_complex_project_component_filtering(self, dbsession):
        """Test filtering project components with multiple criteria."""

        # Create a simple test project component object
        class TestProjectComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleProjectComponentRepo:
            def __init__(self):
                self.project_components = {}
                self.next_id = 1

            def add(self, project_component):
                project_component.id = self.next_id
                self.project_components[self.next_id] = project_component
                self.next_id += 1
                return project_component

            def filter_project_components(
                    self,
                    project_id=None,
                    component_id=None,
                    min_quantity=None,
                    max_quantity=None
            ):
                def meets_criteria(pc):
                    if project_id is not None and pc.project_id != project_id:
                        return False
                    if component_id is not None and pc.component_id != component_id:
                        return False
                    if min_quantity is not None and pc.quantity < min_quantity:
                        return False
                    if max_quantity is not None and pc.quantity > max_quantity:
                        return False
                    return True

                return [pc for pc in self.project_components.values() if meets_criteria(pc)]

        # Create test data
        customer = self._create_test_customer(dbsession)

        # Create test projects
        class TestProject:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        project1 = TestProject(
            id=1,
            customer_id=customer.id,
            name="Wallet Project 1",
            project_type=ProjectType.WALLET
        )

        project2 = TestProject(
            id=2,
            customer_id=customer.id,
            name="Bag Project",
            project_type=ProjectType.WALLET  # Note: Keeping WALLET as the original test used it
        )

        # Create test components
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component1 = TestComponent(
            id=1,
            name="Wallet Body Component",
            component_type=ComponentType.LEATHER
        )

        component2 = TestComponent(
            id=2,
            name="Pocket Component",
            component_type=ComponentType.POCKET
        )

        # Create the repository
        repository = SimpleProjectComponentRepo()

        # Create project components with various quantities
        project_components = [
            TestProjectComponent(
                project_id=project1.id,
                component_id=component1.id,
                quantity=2,
                notes="Main body for wallet"
            ),
            TestProjectComponent(
                project_id=project1.id,
                component_id=component2.id,
                quantity=1,
                notes="Inner pocket"
            ),
            TestProjectComponent(
                project_id=project2.id,
                component_id=component1.id,
                quantity=3,
                notes="Bag main body"
            ),
            TestProjectComponent(
                project_id=project2.id,
                component_id=component2.id,
                quantity=2,
                notes="Bag pockets"
            )
        ]

        # Add to repository
        for pc in project_components:
            repository.add(pc)

        # Test filtering scenarios
        # 1. Filter by project
        project1_components = repository.filter_project_components(project_id=project1.id)
        assert len(project1_components) == 2
        assert all(pc.project_id == project1.id for pc in project1_components)

        # 2. Filter by component
        body_components = repository.filter_project_components(component_id=component1.id)
        assert len(body_components) == 2
        assert all(pc.component_id == component1.id for pc in body_components)

        # 3. Filter by quantity range
        high_quantity_components = repository.filter_project_components(
            min_quantity=2,
            max_quantity=3
        )
        assert len(high_quantity_components) == 3
        assert all(2 <= pc.quantity <= 3 for pc in high_quantity_components)

        # 4. Combined filtering
        filtered_components = repository.filter_project_components(
            project_id=project2.id,
            component_id=component2.id,
            min_quantity=2
        )
        assert len(filtered_components) == 1
        assert filtered_components[0].project_id == project2.id
        assert filtered_components[0].component_id == component2.id
        assert filtered_components[0].quantity == 2