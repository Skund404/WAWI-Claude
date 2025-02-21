# File: tests/test_database/test_manager_factory.py
# Purpose: Test manager factory functionality and edge cases

import pytest
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

from store_management.database.sqlalchemy.base_manager import BaseManager
from store_management.database.sqlalchemy.manager_factory import (
    get_manager,
    register_specialized_manager,
    clear_manager_cache
)

# Create a test base and model for factory testing
FactoryTestBase = declarative_base()


class FactoryTestModel(FactoryTestBase):
    """
    Test model for manager factory tests.
    """
    __tablename__ = 'factory_test_models'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    value = Column(Integer)


class CustomTestManager(BaseManager[FactoryTestModel]):
    """
    Specialized test manager with additional method.
    """

    def custom_method(self) -> str:
        """
        Custom method to test specialized manager functionality.

        Returns:
            A test string
        """
        return "Custom Manager Method"


class TestManagerFactory:
    """
    Comprehensive test suite for manager factory.
    """

    @pytest.fixture(scope='function')
    def test_engine(self):
        """
        Create an in-memory SQLite database for testing.
        """
        engine = create_engine('sqlite:///:memory:')
        FactoryTestBase.metadata.create_all(engine)
        return engine

    @pytest.fixture(scope='function')
    def session_factory(self, test_engine):
        """
        Create a session factory for testing.
        """
        return sessionmaker(bind=test_engine)

    def test_manager_cache(self, session_factory):
        """
        Test manager caching mechanism.
        """
        # Clear existing cache
        clear_manager_cache()

        # Get first manager instance
        first_manager = get_manager(FactoryTestModel, session_factory)

        # Get second manager instance
        second_manager = get_manager(FactoryTestModel, session_factory)

        # Verify same instance is returned
        assert first_manager is second_manager

    def test_specialized_manager_registration(self, session_factory):
        """
        Test registering and using a specialized manager.
        """
        # Register custom manager
        register_specialized_manager(FactoryTestModel, CustomTestManager)

        # Get manager with custom implementation
        manager = get_manager(FactoryTestModel, session_factory)

        # Verify it's the custom manager type
        assert isinstance(manager, CustomTestManager)

        # Test custom method
        assert manager.custom_method() == "Custom Manager Method"

    def test_force_new_manager(self, session_factory):
        """
        Test creating a new manager instance bypassing cache.
        """
        # Clear existing cache
        clear_manager_cache()

        # Get first manager instance
        first_manager = get_manager(FactoryTestModel, session_factory)

        # Get new manager instance, forcing creation
        second_manager = get_manager(
            FactoryTestModel,
            session_factory,
            force_new=True
        )

        # Verify different instances
        assert first_manager is not second_manager

    def test_manager_with_mixins(self, session_factory):
        """
        Test creating a manager with additional mixins.
        """

        # Create a test mixin
        class TestMixin:
            def test_mixin_method(self):
                return "Mixin Method"

        # Get manager with additional mixin
        manager = get_manager(
            FactoryTestModel,
            session_factory,
            mixins=[TestMixin]
        )

        # Verify mixin method exists
        assert hasattr(manager, 'test_mixin_method')
        assert manager.test_mixin_method() == "Mixin Method"

    def test_invalid_mixin(self, session_factory):
        """
        Test handling of invalid mixins.
        """

        # Create an invalid mixin (without __init__)
        class InvalidMixin:
            def some_method(self):
                pass

        # Get manager with invalid mixin (should not raise error)
        manager = get_manager(
            FactoryTestModel,
            session_factory,
            mixins=[InvalidMixin]
        )

        # Basic sanity check
        assert isinstance(manager, BaseManager)


# Performance and Stress Testing
class TestManagerPerformance:
    """
    Performance-oriented tests for manager operations.
    """

    @pytest.fixture(scope='function')
    def large_dataset_manager(self, session_factory):
        """
        Create a manager with a large dataset.
        """
        manager = get_manager(FactoryTestModel, session_factory)

        # Create a large number of records
        large_dataset = [
            {'name': f'Record {i}', 'value': i}
            for i in range(1000)
        ]
        manager.bulk_create(large_dataset)

        return manager

    def test_large_dataset_retrieval(self, large_dataset_manager):
        """
        Test performance of retrieving large datasets.
        """
        # Retrieve all records
        all_records = large_dataset_manager.get_all()

        # Verify total count
        assert len(all_records) == 1000

    def test_large_dataset_filtering(self, large_dataset_manager):
        """
        Test filtering performance on large datasets.
        """
        # Complex filtering
        filtered_records = large_dataset_manager.filter_complex([
            {'field': 'value', 'op': '>', 'value': 500}
        ])

        # Verify filtering
        assert len(filtered_records) == 499
        assert all(record.value > 500 for record in filtered_records)