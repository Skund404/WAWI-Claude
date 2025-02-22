# File: tests/test_database/test_base_manager.py
# Purpose: Comprehensive unit tests for BaseManager and related components

import pytest
from typing import List, Dict, Any
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Import the components to test
from database.sqlalchemy.base_manager import BaseManager
from database.sqlalchemy.manager_factory import (
    get_manager,
    register_specialized_manager,
    clear_manager_cache
)
from utils.error_handling import DatabaseError

# Create a test base and model
TestBase = declarative_base()


class TestModel(TestBase):
    """
    Test model for BaseManager unit tests.
    """
    __tablename__ = 'test_models'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)


class TestSpecializedManager(BaseManager[TestModel]):
    """
    Specialized test manager with additional method.
    """

    def get_by_name(self, name: str) -> List[TestModel]:
        """
        Retrieve models by name.

        Args:
            name: Name to search for

        Returns:
            List of matching models
        """
        return self.filter_by_multiple({'name': name})


@pytest.fixture(scope='function')
def test_engine():
    """
    Create an in-memory SQLite database for testing.
    """
    engine = create_engine('sqlite:///:memory:')
    TestBase.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='function')
def session_factory(test_engine):
    """
    Create a session factory for testing.
    """
    return sessionmaker(bind=test_engine)


@pytest.fixture(scope='function')
def test_manager(session_factory):
    """
    Create a BaseManager instance for testing.
    """
    # Clear any existing cached managers
    clear_manager_cache()

    # Register the specialized manager
    register_specialized_manager(TestModel, TestSpecializedManager)

    # Get the manager
    return get_manager(TestModel, session_factory)


class TestBaseManager:
    """
    Comprehensive test suite for BaseManager.
    """

    def test_create_single_record(self, test_manager):
        """
        Test creating a single record.
        """
        # Create a record
        record = test_manager.create({
            'name': 'Test Record',
            'value': 100
        })

        # Verify record creation
        assert record is not None
        assert record.name == 'Test Record'
        assert record.value == 100
        assert record.id is not None

    def test_get_record(self, test_manager):
        """
        Test retrieving a single record by ID.
        """
        # Create a record first
        created_record = test_manager.create({
            'name': 'Retrieve Test',
            'value': 200
        })

        # Retrieve the record
        retrieved_record = test_manager.get(created_record.id)

        # Verify retrieval
        assert retrieved_record is not None
        assert retrieved_record.id == created_record.id
        assert retrieved_record.name == 'Retrieve Test'

    def test_update_record(self, test_manager):
        """
        Test updating an existing record.
        """
        # Create a record
        record = test_manager.create({
            'name': 'Original Name',
            'value': 300
        })

        # Update the record
        updated_record = test_manager.update(record.id, {
            'name': 'Updated Name',
            'value': 400
        })

        # Verify update
        assert updated_record is not None
        assert updated_record.name == 'Updated Name'
        assert updated_record.value == 400

    def test_delete_record(self, test_manager):
        """
        Test deleting a record.
        """
        # Create a record
        record = test_manager.create({
            'name': 'Delete Test',
            'value': 500
        })

        # Delete the record
        delete_result = test_manager.delete(record.id)

        # Verify deletion
        assert delete_result is True

        # Ensure record is actually deleted
        retrieved_record = test_manager.get(record.id)
        assert retrieved_record is None

    def test_bulk_create(self, test_manager):
        """
        Test bulk creation of records.
        """
        # Bulk create records
        records = test_manager.bulk_create([
            {'name': 'Bulk 1', 'value': 600},
            {'name': 'Bulk 2', 'value': 700},
            {'name': 'Bulk 3', 'value': 800}
        ])

        # Verify bulk creation
        assert len(records) == 3
        assert all(record.id is not None for record in records)
        assert [record.name for record in records] == ['Bulk 1', 'Bulk 2', 'Bulk 3']

    def test_bulk_update(self, test_manager):
        """
        Test bulk updating of records.
        """
        # Create initial records
        initial_records = test_manager.bulk_create([
            {'name': 'Update 1', 'value': 900},
            {'name': 'Update 2', 'value': 1000}
        ])

        # Bulk update
        update_count = test_manager.bulk_update([
            {'id': initial_records[0].id, 'name': 'Updated 1', 'value': 1100},
            {'id': initial_records[1].id, 'name': 'Updated 2', 'value': 1200}
        ])

        # Verify bulk update
        assert update_count == 2

        # Verify individual record updates
        updated_record1 = test_manager.get(initial_records[0].id)
        updated_record2 = test_manager.get(initial_records[1].id)

        assert updated_record1.name == 'Updated 1'
        assert updated_record1.value == 1100
        assert updated_record2.name == 'Updated 2'
        assert updated_record2.value == 1200

    def test_get_all(self, test_manager):
        """
        Test retrieving all records.
        """
        # Create multiple records
        test_manager.bulk_create([
            {'name': 'Record 1', 'value': 1},
            {'name': 'Record 2', 'value': 2},
            {'name': 'Record 3', 'value': 3}
        ])

        # Retrieve all records
        all_records = test_manager.get_all()

        # Verify retrieval
        assert len(all_records) == 3

    def test_search(self, test_manager):
        """
        Test search functionality.
        """
        # Create test records
        test_manager.bulk_create([
            {'name': 'Search Test 1', 'value': 2000},
            {'name': 'Search Test 2', 'value': 2100},
            {'name': 'Other Record', 'value': 2200}
        ])

        # Perform search
        search_results = test_manager.search('Search')

        # Verify search results
        assert len(search_results) == 2
        assert all('Search' in record.name for record in search_results)

    def test_filter(self, test_manager):
        """
        Test complex filtering.
        """
        # Create test records
        test_manager.bulk_create([
            {'name': 'Filter 1', 'value': 3000},
            {'name': 'Filter 2', 'value': 3100},
            {'name': 'Filter 3', 'value': 3200}
        ])

        # Filter by multiple conditions
        filtered_records = test_manager.filter_by_multiple({
            'name': 'Filter 1'
        })

        # Verify filtering
        assert len(filtered_records) == 1
        assert filtered_records[0].name == 'Filter 1'

    def test_exists(self, test_manager):
        """
        Test existence check.
        """
        # Create a test record
        test_manager.create({
            'name': 'Exists Test',
            'value': 4000
        })

        # Check existence
        exists_result = test_manager.exists(name='Exists Test')
        not_exists_result = test_manager.exists(name='Non-Existent')

        # Verify existence checks
        assert exists_result is True
        assert not_exists_result is False

    def test_count(self, test_manager):
        """
        Test record counting.
        """
        # Create multiple records
        test_manager.bulk_create([
            {'name': 'Count 1', 'value': 5000},
            {'name': 'Count 2', 'value': 5100},
            {'name': 'Count 3', 'value': 5200}
        ])

        # Count total records
        total_count = test_manager.count()

        # Count filtered records
        filtered_count = test_manager.count(name='Count 1')

        # Verify counts
        assert total_count == 3
        assert filtered_count == 1

    def test_specialized_manager(self, session_factory):
        """
        Test specialized manager functionality.
        """
        # Get the specialized manager
        specialized_manager = get_manager(TestModel, session_factory)

        # Create test records
        specialized_manager.bulk_create([
            {'name': 'Special 1', 'value': 6000},
            {'name': 'Special 2', 'value': 6100},
            {'name': 'Special 1', 'value': 6200}
        ])

        # Use specialized method
        special_records = specialized_manager.get_by_name('Special 1')

        # Verify specialized method
        assert len(special_records) == 2
        assert all(record.name == 'Special 1' for record in special_records)


class TestErrorHandling:
    """
    Test error handling scenarios.
    """

    def test_create_invalid_data(self, test_manager):
        """
        Test creating record with invalid data.
        """
        with pytest.raises(DatabaseError):
            # Attempt to create record with non-existent column
            test_manager.create({
                'non_existent_column': 'Invalid Data'
            })

    def test_update_non_existent_record(self, test_manager):
        """
        Test updating a non-existent record.
        """
        # Attempt to update non-existent record
        updated_record = test_manager.update(9999, {
            'name': 'Non-Existent Update'
        })

        # Verify no update occurs
        assert updated_record is None

    def test_delete_non_existent_record(self, test_manager):
        """
        Test deleting a non-existent record.
        """
        # Attempt to delete non-existent record
        delete_result = test_manager.delete(9999)

        # Verify deletion fails gracefully
        assert delete_result is False