from database.models.base import metadata
# test_mixin_performance.py
import time
import pytest
from sqlalchemy import Column, Integer, String, create_engine, select, and_
from sqlalchemy.orm import declarative_base, sessionmaker

from di.core import inject
from services.interfaces import MaterialService
from base_mixins import SearchMixin, FilterMixin, PaginationMixin, TransactionMixin

TestBase = declarative_base()
TestBase.metadata = metadata


class PerformanceTestModel(TestBase):
    """Large test model for performance benchmarking."""
    __tablename__ = 'performance_test_models'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    category = Column(String)
    status = Column(String)
    value = Column(Integer)


class PerformanceTestManager(SearchMixin, FilterMixin, PaginationMixin, TransactionMixin):
    """Performance test manager combining mixins."""

    def __init__(self, model_class, session_factory):
        """Initialize the performance test manager."""
        super().__init__(model_class, session_factory)


@pytest.fixture(scope='module')
def test_engine():
    """Create an in-memory SQLite database for performance testing."""
    engine = create_engine('sqlite:///:memory:')
    TestBase.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='module')
def session_factory(test_engine):
    """Create a session factory for performance testing."""
    return sessionmaker(bind=test_engine)


@pytest.fixture(scope='module')
def performance_manager(session_factory):
    """Create a performance test manager instance."""
    return PerformanceTestManager(PerformanceTestModel, session_factory)


@pytest.fixture(scope='module')
def large_dataset(performance_manager):
    """Populate test database with a large dataset."""

    def _populate(session):
        records = [
            PerformanceTestModel(
                name=f'Item {i}',
                category='test' if i % 5 == 0 else 'regular',
                status='active' if i % 3 == 0 else 'inactive',
                value=i
            )
            for i in range(10000)
        ]
        session.add_all(records)
        session.commit()

    performance_manager.run_in_transaction(_populate)
    return True


class TestMixinPerformance:
    """Performance benchmarking for database mixins."""

    def test_search_performance(self, performance_manager, large_dataset):
        """Benchmark search performance."""
        start_time = time.time()
        results = performance_manager.search('Item')
        search_time = time.time() - start_time

        assert len(results) > 0
        assert search_time < 0.5, f'Search took {search_time} seconds, expected < 0.5'

    def test_advanced_search_performance(self, performance_manager, large_dataset):
        """Benchmark advanced search performance."""
        start_time = time.time()
        results = performance_manager.advanced_search({
            'category': {'op': '==', 'value': 'test'},
            'value': {'op': '>', 'value': 1000}
        })
        search_time = time.time() - start_time

        assert len(results) > 0
        assert search_time < 0.5, f'Advanced search took {search_time} seconds, expected < 0.5'

    def test_filter_performance(self, performance_manager, large_dataset):
        """Benchmark filtering performance."""
        start_time = time.time()
        results = performance_manager.filter_by_multiple({
            'status': 'active',
            'category': 'test'
        })
        filter_time = time.time() - start_time

        assert len(results) > 0
        assert filter_time < 0.5, f'Filtering took {filter_time} seconds, expected < 0.5'

    def test_pagination_performance(self, performance_manager, large_dataset):
        """Benchmark pagination performance."""
        start_time = time.time()
        results = performance_manager.get_paginated(
            page=2,
            page_size=100,
            order_by='value',
            filters={'status': 'active'}
        )
        pagination_time = time.time() - start_time

        assert len(results['items']) == 100
        assert pagination_time < 0.5, f'Pagination took {pagination_time} seconds, expected < 0.5'

    def test_complex_filter_performance(self, performance_manager, large_dataset):
        """Benchmark complex filtering performance."""
        start_time = time.time()
        results = performance_manager.filter_complex([
            {'field': 'status', 'op': '==', 'value': 'active'},
            {'field': 'category', 'op': '==', 'value': 'test'},
            {'field': 'value', 'op': '>', 'value': 500}
        ])
        complex_filter_time = time.time() - start_time

        assert len(results) > 0
        assert complex_filter_time < 0.5, f'Complex filtering took {complex_filter_time} seconds, expected < 0.5'

    def test_native_sqlalchemy_performance_comparison(self, performance_manager, large_dataset):
        """Compare mixin performance with native SQLAlchemy query."""
        # Test mixin approach
        mixin_start_time = time.time()
        mixin_results = performance_manager.filter_complex([
            {'field': 'status', 'op': '==', 'value': 'active'},
            {'field': 'category', 'op': '==', 'value': 'test'},
            {'field': 'value', 'op': '>', 'value': 500}
        ])
        mixin_time = time.time() - mixin_start_time

        # Test native SQLAlchemy approach
        with performance_manager.session_factory() as session:
            native_start_time = time.time()
            native_query = select(PerformanceTestModel).where(and_(
                PerformanceTestModel.status == 'active',
                PerformanceTestModel.category == 'test',
                PerformanceTestModel.value > 500
            ))
            native_results = session.execute(native_query).scalars().all()
            native_time = time.time() - native_start_time

        # Compare results
        assert len(mixin_results) == len(native_results)
        assert mixin_time < 1.0, f'Mixin query took {mixin_time} seconds, expected < 1.0'
        assert native_time < 1.0, f'Native query took {native_time} seconds, expected < 1.0'