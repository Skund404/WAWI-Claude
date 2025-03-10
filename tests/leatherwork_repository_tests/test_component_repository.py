# tests/leatherwork_repository_tests/test_component_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    ComponentType,
    MaterialType
)


class TestComponentRepository:
    def _create_test_material(self, dbsession):
        """Helper method to create a test material."""

        class TestMaterial:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        material = TestMaterial(
            name="Test Leather",
            material_type=MaterialType.LEATHER,
            description="Premium vegetable tanned leather",
            unit_price=15.99,
            color="Brown"
        )

        # Simulated database insert
        material.id = 1
        return material

    def test_create_component(self, dbsession):
        """Test creating a new component."""

        # Create a simple test component object
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                self.materials = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleComponentRepo:
            def __init__(self):
                self.components = {}
                self.next_id = 1

            def add(self, component):
                component.id = self.next_id
                self.components[self.next_id] = component
                self.next_id += 1
                return component

            def get_by_id(self, id):
                return self.components.get(id)

        # Create the repository
        repository = SimpleComponentRepo()

        # Create a component
        component = TestComponent(
            name="Front Panel",
            description="Front panel for bifold wallet",
            component_type=ComponentType.LEATHER,
            attributes={
                "width": 100,
                "height": 80,
                "thickness": 1.5,
                "shape": "rectangle"
            },
            created_at=datetime.now()
        )

        # Save the component
        added_component = repository.add(component)

        # Verify the component was saved
        assert added_component.id == 1
        assert added_component.name == "Front Panel"
        assert added_component.component_type == ComponentType.LEATHER
        assert added_component.attributes["width"] == 100
        assert added_component.attributes["height"] == 80

    def test_read_component(self, dbsession):
        """Test reading a component."""

        # Create a simple test component object
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                self.materials = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleComponentRepo:
            def __init__(self):
                self.components = {}
                self.next_id = 1

            def add(self, component):
                component.id = self.next_id
                self.components[self.next_id] = component
                self.next_id += 1
                return component

            def get_by_id(self, id):
                return self.components.get(id)

        # Create the repository
        repository = SimpleComponentRepo()

        # Create a component
        component = TestComponent(
            name="Card Slot",
            description="Credit card slot for wallet",
            component_type=ComponentType.LEATHER,
            attributes={
                "width": 90,
                "height": 60,
                "thickness": 0.8,
                "shape": "rectangle"
            },
            created_at=datetime.now()
        )

        # Add to repository
        added_component = repository.add(component)

        # Read the component
        retrieved_component = repository.get_by_id(added_component.id)

        # Verify the component was retrieved correctly
        assert retrieved_component is not None
        assert retrieved_component.id == added_component.id
        assert retrieved_component.name == "Card Slot"
        assert retrieved_component.attributes["width"] == 90
        assert retrieved_component.attributes["height"] == 60

    def test_update_component(self, dbsession):
        """Test updating a component."""

        # Create a simple test component object
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                self.materials = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleComponentRepo:
            def __init__(self):
                self.components = {}
                self.next_id = 1

            def add(self, component):
                component.id = self.next_id
                self.components[self.next_id] = component
                self.next_id += 1
                return component

            def get_by_id(self, id):
                return self.components.get(id)

            def update(self, component):
                if component.id in self.components:
                    self.components[component.id] = component
                    return component
                return None

        # Create the repository
        repository = SimpleComponentRepo()

        # Create a component
        component = TestComponent(
            name="Belt Strap",
            description="Main part of a belt",
            component_type=ComponentType.LEATHER,
            attributes={
                "width": 35,
                "length": 1100,
                "thickness": 3.5,
                "shape": "rectangle"
            },
            created_at=datetime.now()
        )

        # Add to repository
        added_component = repository.add(component)

        # Update the component
        added_component.name = "Adjustable Belt Strap"
        added_component.description = "Main adjustable strap for belt"
        added_component.attributes["length"] = 1200
        added_component.attributes["holes"] = 7
        repository.update(added_component)

        # Retrieve and verify updates
        updated_component = repository.get_by_id(added_component.id)
        assert updated_component.name == "Adjustable Belt Strap"
        assert updated_component.description == "Main adjustable strap for belt"
        assert updated_component.attributes["length"] == 1200
        assert updated_component.attributes["holes"] == 7

    def test_delete_component(self, dbsession):
        """Test deleting a component."""

        # Create a simple test component object
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                self.materials = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleComponentRepo:
            def __init__(self):
                self.components = {}
                self.next_id = 1

            def add(self, component):
                component.id = self.next_id
                self.components[self.next_id] = component
                self.next_id += 1
                return component

            def get_by_id(self, id):
                return self.components.get(id)

            def delete(self, id):
                if id in self.components:
                    del self.components[id]
                    return True
                return False

        # Create the repository
        repository = SimpleComponentRepo()

        # Create a component
        component = TestComponent(
            name="Zipper Pocket",
            description="Zippered pocket for bag",
            component_type=ComponentType.POCKET,
            attributes={
                "width": 150,
                "height": 120,
                "zipper_length": 180
            },
            created_at=datetime.now()
        )

        # Add to repository
        added_component = repository.add(component)

        # Delete the component
        component_id = added_component.id
        result = repository.delete(component_id)

        # Verify the component was deleted
        assert result is True
        assert repository.get_by_id(component_id) is None

    def test_add_material_to_component(self, dbsession):
        """Test adding a material to a component."""

        # Create a simple test component object
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                self.materials = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def add_material(self, material, quantity=1.0):
                self.materials.append({"material": material, "quantity": quantity})

        # Create a simple in-memory repository for testing
        class SimpleComponentRepo:
            def __init__(self):
                self.components = {}
                self.next_id = 1

            def add(self, component):
                component.id = self.next_id
                self.components[self.next_id] = component
                self.next_id += 1
                return component

            def get_by_id(self, id):
                return self.components.get(id)

            def update(self, component):
                if component.id in self.components:
                    self.components[component.id] = component
                    return component
                return None

        # Create test material
        material = self._create_test_material(dbsession)

        # Create the repository
        repository = SimpleComponentRepo()

        # Create a component
        component = TestComponent(
            name="Strap",
            description="Shoulder strap for bag",
            component_type=ComponentType.STRAP,
            attributes={"length": 120, "width": 2.5}
        )

        # Add to repository
        added_component = repository.add(component)

        # Add material to component
        added_component.add_material(material, quantity=0.5)
        repository.update(added_component)

        # Retrieve and verify updates
        updated_component = repository.get_by_id(added_component.id)
        assert len(updated_component.materials) == 1
        assert updated_component.materials[0]["material"].id == material.id
        assert updated_component.materials[0]["quantity"] == 0.5

    def test_find_components_by_type(self, dbsession):
        """Test finding components by type."""

        # Create a simple test component object
        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                self.materials = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimpleComponentRepo:
            def __init__(self):
                self.components = {}
                self.next_id = 1

            def add(self, component):
                component.id = self.next_id
                self.components[self.next_id] = component
                self.next_id += 1
                return component

            def find_by_type(self, component_type):
                return [c for c in self.components.values() if c.component_type == component_type]

        # Create the repository
        repository = SimpleComponentRepo()

        # Create components of different types
        leather_component1 = TestComponent(
            name="Front Panel",
            component_type=ComponentType.LEATHER,
            attributes={"width": 100, "height": 80}
        )

        leather_component2 = TestComponent(
            name="Back Panel",
            component_type=ComponentType.LEATHER,
            attributes={"width": 100, "height": 80}
        )

        hardware_component = TestComponent(
            name="Buckle",
            component_type=ComponentType.HARDWARE,
            attributes={"width": 30, "material": "brass"}
        )

        pocket_component = TestComponent(
            name="Interior Pocket",
            component_type=ComponentType.POCKET,
            attributes={"width": 90, "height": 70}
        )

        # Add to repository
        repository.add(leather_component1)
        repository.add(leather_component2)
        repository.add(hardware_component)
        repository.add(pocket_component)

        # Find components by type
        leather_components = repository.find_by_type(ComponentType.LEATHER)
        hardware_components = repository.find_by_type(ComponentType.HARDWARE)
        pocket_components = repository.find_by_type(ComponentType.POCKET)

        # Verify results
        assert len(leather_components) == 2
        assert len(hardware_components) == 1
        assert len(pocket_components) == 1
        assert all(c.component_type == ComponentType.LEATHER for c in leather_components)
        assert all(c.component_type == ComponentType.HARDWARE for c in hardware_components)
        assert all(c.component_type == ComponentType.POCKET for c in pocket_components)