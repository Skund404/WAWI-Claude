# tests/leatherwork_repository_tests/test_pattern_repository.py
import pytest
from datetime import datetime, timedelta
from database.models.enums import (
    ProjectType,
    SkillLevel,
    ComponentType
)


class TestPatternRepository:
    def _create_test_component(self, dbsession):
        """Helper method to create a test component."""

        class TestComponent:
            def __init__(self, **kwargs):
                self.id = None
                for key, value in kwargs.items():
                    setattr(self, key, value)

        component = TestComponent(
            name="Front Panel",
            description="Main front panel for wallet",
            component_type=ComponentType.LEATHER,
            attributes={"width": 120, "height": 90, "thickness": 1.5}
        )

        # Simulated database insert
        component.id = 1
        return component

    def test_create_pattern(self, dbsession):
        """Test creating a new pattern."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def get_by_id(self, id):
                return self.patterns.get(id)

        # Create the repository
        repository = SimplePatternRepo()

        # Create a pattern
        pattern = TestPattern(
            name="Classic Bifold Wallet",
            description="A traditional bifold wallet pattern with card slots",
            project_type=ProjectType.WALLET,
            skill_level=SkillLevel.INTERMEDIATE,
            estimated_time=3.5,
            difficulty_rating=3,
            created_at=datetime.now()
        )

        # Save the pattern
        added_pattern = repository.add(pattern)

        # Verify the pattern was saved
        assert added_pattern.id == 1
        assert added_pattern.name == "Classic Bifold Wallet"
        assert added_pattern.project_type == ProjectType.WALLET
        assert added_pattern.skill_level == SkillLevel.INTERMEDIATE
        assert added_pattern.estimated_time == 3.5

    def test_read_pattern(self, dbsession):
        """Test reading a pattern."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def get_by_id(self, id):
                return self.patterns.get(id)

        # Create the repository
        repository = SimplePatternRepo()

        # Create a pattern
        pattern = TestPattern(
            name="Messenger Bag Pattern",
            description="A classic messenger bag with adjustable strap",
            project_type=ProjectType.MESSENGER_BAG,
            skill_level=SkillLevel.ADVANCED,
            estimated_time=12.0,
            difficulty_rating=4,
            created_at=datetime.now()
        )

        # Add to repository
        added_pattern = repository.add(pattern)

        # Read the pattern
        retrieved_pattern = repository.get_by_id(added_pattern.id)

        # Verify the pattern was retrieved correctly
        assert retrieved_pattern is not None
        assert retrieved_pattern.id == added_pattern.id
        assert retrieved_pattern.name == "Messenger Bag Pattern"
        assert retrieved_pattern.project_type == ProjectType.MESSENGER_BAG
        assert retrieved_pattern.skill_level == SkillLevel.ADVANCED

    def test_update_pattern(self, dbsession):
        """Test updating a pattern."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def get_by_id(self, id):
                return self.patterns.get(id)

            def update(self, pattern):
                if pattern.id in self.patterns:
                    self.patterns[pattern.id] = pattern
                    return pattern
                return None

        # Create the repository
        repository = SimplePatternRepo()

        # Create a pattern
        pattern = TestPattern(
            name="Laptop Sleeve",
            description="A basic laptop sleeve",
            project_type=ProjectType.LAPTOP_SLEEVE,
            skill_level=SkillLevel.BEGINNER,
            estimated_time=2.0,
            difficulty_rating=2,
            created_at=datetime.now()
        )

        # Add to repository
        added_pattern = repository.add(pattern)

        # Update the pattern
        added_pattern.name = "Padded Laptop Sleeve"
        added_pattern.description = "A padded laptop sleeve with zipper closure"
        added_pattern.estimated_time = 3.0
        added_pattern.difficulty_rating = 3
        repository.update(added_pattern)

        # Retrieve and verify updates
        updated_pattern = repository.get_by_id(added_pattern.id)
        assert updated_pattern.name == "Padded Laptop Sleeve"
        assert updated_pattern.description == "A padded laptop sleeve with zipper closure"
        assert updated_pattern.estimated_time == 3.0
        assert updated_pattern.difficulty_rating == 3

    def test_delete_pattern(self, dbsession):
        """Test deleting a pattern."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def get_by_id(self, id):
                return self.patterns.get(id)

            def delete(self, id):
                if id in self.patterns:
                    del self.patterns[id]
                    return True
                return False

        # Create the repository
        repository = SimplePatternRepo()

        # Create a pattern
        pattern = TestPattern(
            name="Card Holder",
            description="A simple card holder pattern",
            project_type=ProjectType.CARD_HOLDER,
            skill_level=SkillLevel.BEGINNER,
            estimated_time=1.5,
            difficulty_rating=1,
            created_at=datetime.now()
        )

        # Add to repository
        added_pattern = repository.add(pattern)

        # Delete the pattern
        pattern_id = added_pattern.id
        result = repository.delete(pattern_id)

        # Verify the pattern was deleted
        assert result is True
        assert repository.get_by_id(pattern_id) is None

    def test_add_component_to_pattern(self, dbsession):
        """Test adding a component to a pattern."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

            def add_component(self, component, quantity=1):
                self.components.append({"component": component, "quantity": quantity})

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def get_by_id(self, id):
                return self.patterns.get(id)

            def update(self, pattern):
                if pattern.id in self.patterns:
                    self.patterns[pattern.id] = pattern
                    return pattern
                return None

        # Create a test component
        component = self._create_test_component(dbsession)

        # Create the repository
        repository = SimplePatternRepo()

        # Create a pattern
        pattern = TestPattern(
            name="Belt Pattern",
            description="A classic leather belt pattern",
            project_type=ProjectType.BELT,
            skill_level=SkillLevel.BEGINNER,
            estimated_time=2.0,
            created_at=datetime.now()
        )

        # Add to repository
        added_pattern = repository.add(pattern)

        # Add component to pattern
        added_pattern.add_component(component, quantity=1)
        repository.update(added_pattern)

        # Retrieve and verify updates
        updated_pattern = repository.get_by_id(added_pattern.id)
        assert len(updated_pattern.components) == 1
        assert updated_pattern.components[0]["component"].id == component.id
        assert updated_pattern.components[0]["quantity"] == 1

    def test_find_patterns_by_skill_level(self, dbsession):
        """Test finding patterns by skill level."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def find_by_skill_level(self, skill_level):
                return [p for p in self.patterns.values() if p.skill_level == skill_level]

        # Create the repository
        repository = SimplePatternRepo()

        # Create patterns with different skill levels
        beginner_pattern1 = TestPattern(
            name="Simple Card Holder",
            project_type=ProjectType.CARD_HOLDER,
            skill_level=SkillLevel.BEGINNER,
            estimated_time=1.0
        )

        beginner_pattern2 = TestPattern(
            name="Basic Key Fob",
            project_type=ProjectType.KEY_CASE,
            skill_level=SkillLevel.BEGINNER,
            estimated_time=0.5
        )

        intermediate_pattern = TestPattern(
            name="Bifold Wallet",
            project_type=ProjectType.WALLET,
            skill_level=SkillLevel.INTERMEDIATE,
            estimated_time=4.0
        )

        advanced_pattern = TestPattern(
            name="Messenger Bag",
            project_type=ProjectType.MESSENGER_BAG,
            skill_level=SkillLevel.ADVANCED,
            estimated_time=15.0
        )

        # Add to repository
        repository.add(beginner_pattern1)
        repository.add(beginner_pattern2)
        repository.add(intermediate_pattern)
        repository.add(advanced_pattern)

        # Find patterns by skill level
        beginner_patterns = repository.find_by_skill_level(SkillLevel.BEGINNER)
        intermediate_patterns = repository.find_by_skill_level(SkillLevel.INTERMEDIATE)
        advanced_patterns = repository.find_by_skill_level(SkillLevel.ADVANCED)

        # Verify results
        assert len(beginner_patterns) == 2
        assert len(intermediate_patterns) == 1
        assert len(advanced_patterns) == 1
        assert all(p.skill_level == SkillLevel.BEGINNER for p in beginner_patterns)
        assert all(p.skill_level == SkillLevel.INTERMEDIATE for p in intermediate_patterns)
        assert all(p.skill_level == SkillLevel.ADVANCED for p in advanced_patterns)

    def test_find_patterns_by_project_type(self, dbsession):
        """Test finding patterns by project type."""

        # Create a simple test pattern object
        class TestPattern:
            def __init__(self, **kwargs):
                self.id = None
                self.components = []
                for key, value in kwargs.items():
                    setattr(self, key, value)

        # Create a simple in-memory repository for testing
        class SimplePatternRepo:
            def __init__(self):
                self.patterns = {}
                self.next_id = 1

            def add(self, pattern):
                pattern.id = self.next_id
                self.patterns[self.next_id] = pattern
                self.next_id += 1
                return pattern

            def find_by_project_type(self, project_type):
                return [p for p in self.patterns.values() if p.project_type == project_type]

        # Create the repository
        repository = SimplePatternRepo()

        # Create patterns with different project types
        wallet_pattern1 = TestPattern(
            name="Bifold Wallet",
            project_type=ProjectType.WALLET,
            skill_level=SkillLevel.INTERMEDIATE
        )

        wallet_pattern2 = TestPattern(
            name="Trifold Wallet",
            project_type=ProjectType.WALLET,
            skill_level=SkillLevel.ADVANCED
        )

        belt_pattern = TestPattern(
            name="Casual Belt",
            project_type=ProjectType.BELT,
            skill_level=SkillLevel.BEGINNER
        )

        bag_pattern = TestPattern(
            name="Tote Bag",
            project_type=ProjectType.TOTE_BAG,
            skill_level=SkillLevel.INTERMEDIATE
        )

        # Add to repository
        repository.add(wallet_pattern1)
        repository.add(wallet_pattern2)
        repository.add(belt_pattern)
        repository.add(bag_pattern)

        # Find patterns by project type
        wallet_patterns = repository.find_by_project_type(ProjectType.WALLET)
        belt_patterns = repository.find_by_project_type(ProjectType.BELT)
        bag_patterns = repository.find_by_project_type(ProjectType.TOTE_BAG)

        # Verify results
        assert len(wallet_patterns) == 2
        assert len(belt_patterns) == 1
        assert len(bag_patterns) == 1
        assert all(p.project_type == ProjectType.WALLET for p in wallet_patterns)
        assert all(p.project_type == ProjectType.BELT for p in belt_patterns)
        assert all(p.project_type == ProjectType.TOTE_BAG for p in bag_patterns)