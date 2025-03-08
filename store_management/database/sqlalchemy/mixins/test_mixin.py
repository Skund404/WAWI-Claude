from database.models.base import metadata
# test_mixin.py
import pytest
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from di.core import inject
from services.interfaces import MaterialService
from base_mixins import SearchMixin, FilterMixin, PaginationMixin, TransactionMixin

TestBase = declarative_base()
TestBase.metadata = metadata


class TestModel(TestBase):
    """Test model for mixin testing."""
    __tablename__ = 'test_models'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    status = Column(String)
    value = Column(Integer)


class TestModelManager(SearchMixin, FilterMixin, PaginationMixin, TransactionMixin):
    """Test manager combining all mixins."""

    def __init__(self, model_class, session_factory):
        """Initialize the test manager with all mixins."""
        super().__init__(model_class, session_factory)


@pytest.fixture(scope='function')
def test_engine():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine('sqlite:///:memory:')
    TestBase.metadata.create_all(engine)
    return engine


@pytest.fixture(scope='function')
def session_factory(test_engine):
    """Create a session factory for testing."""
    return sessionmaker(bind=test_engine)


@pytest.fixture(scope='function')
def test_manager(session_factory):
    """Create a test manager instance."""
    return TestModelManager(TestModel, session_factory)


@pytest.fixture(scope='function')
def sample_data(test_manager):
    """Populate test database with sample data."""

    def _populate(session):
        sample_records = [
            TestModel(name='Apple', status='active', value=100),
            TestModel(name='Banana', status='active', value=200),
            TestModel(name='Cherry', status='inactive', value=300),
            TestModel(name='Date', status='active', value=400)
        ]
        session.add_all(sample_records)
        session.commit()

    test_manager.run_in_transaction(_populate)
    return True


class TestSearchMixin:
    """Test suite for SearchMixin functionality."""

    def test_basic_search(self, test_manager, sample_data):
        """Test basic search across all string fields."""
        results = test_manager.search('apple')
        assert len(results) == 1
        assert results[0].name == 'Apple'

    def test_advanced_search(self, test_manager, sample_data):
        """Test advanced search with multiple criteria."""
        results = test_manager.advanced_search({
            'name': {'op': 'like', 'value': '%a%'},
            'value': {'op': '>', 'value': 150}
        })
        assert len(results) == 2
        assert all(result.name in ['Banana', 'Date'] for result in results)


class TestFilterMixin:
    """Test suite for FilterMixin functionality."""

    def test_filter_by_multiple(self, test_manager, sample_data):
        """Test filtering by multiple exact match criteria."""
        results = test_manager.filter_by_multiple({'status': 'active'})
        assert len(results) == 3
        assert all(result.status == 'active' for result in results)

    def test_filter_with_or(self, test_manager, sample_data):
        """Test filtering with OR conditions."""
        results = test_manager.filter_with_or({'name': ['Apple', 'Cherry']})
        assert len(results) == 2
        assert set(result.name for result in results) == {'Apple', 'Cherry'}

    def test_filter_complex(self, test_manager, sample_data):
        """Test complex filtering with multiple conditions."""
        and_results = test_manager.filter_complex([
            {'field': 'status', 'op': '==', 'value': 'active'},
            {'field': 'value', 'op': '>', 'value': 150}
        ])
        assert len(and_results) == 2
        assert all(result.status == 'active' and result.value > 150 for result in and_results)

        or_results = test_manager.filter_complex([
            {'field': 'name', 'op': '==', 'value': 'Apple'},
            {'field': 'name', 'op': '==', 'value': 'Cherry'}
        ], join_type='or')
        assert len(or_results) == 2
        assert set(result.name for result in or_results) == {'Apple', 'Cherry'}


class TestPaginationMixin:
    """Test suite for PaginationMixin functionality."""

    def test_pagination_basic(self, test_manager, session_factory):
        """Test basic pagination functionality."""

        def _populate_more(session):
            more_records = [
                TestModel(name=f'Record {i}', status='active', value=i * 10)
                for i in range(5, 15)
            ]
            session.add_all(more_records)
            session.commit()

        test_manager.run_in_transaction(_populate_more)

        page_1 = test_manager.get_paginated(page=1, page_size=5)
        assert page_1['page'] == 1
        assert page_1['page_size'] == 5
        assert len(page_1['items']) == 5
        assert page_1['total_pages'] == 3
        assert page_1['total_items'] == 14  # 4 from sample_data + 10 added here

    def test_pagination_with_filters(self, test_manager, sample_data):
        """Test pagination with filtering."""
        result = test_manager.get_paginated(
            page=1,
            page_size=2,
            order_by='value',
            filters={'status': 'active'}
        )
        assert len(result['items']) == 2
        assert result['items'][0].name == 'Apple'
        assert result['items'][1].name == 'Banana'


class TestTransactionMixin:
    """Test suite for TransactionMixin functionality."""

    def test_run_in_transaction_success(self, test_manager):
        """Test successful transaction."""

        def _test_transaction(session):
            new_record = TestModel(name='Transaction Test', status='active', value=500)
            session.add(new_record)
            return new_record

        result = test_manager.run_in_transaction(_test_transaction)
        assert result.name == 'Transaction Test'

        with test_manager.session_factory() as session:
            verify_record = session.query(TestModel).filter_by(name='Transaction Test').first()
            assert verify_record is not None

    def test_run_in_transaction_rollback(self, test_manager):
        """Test transaction rollback on error."""

        def _failing_transaction(session):
            new_record = TestModel(name='Rollback Test', status='active', value=600)
            session.add(new_record)
            raise ValueError('Intentional error to test rollback')

        with pytest.raises(ValueError):
            test_manager.run_in_transaction(_failing_transaction)

        with test_manager.session_factory() as session:
            verify_record = session.query(TestModel).filter_by(name='Rollback Test').first()
            assert verify_record is None

    def test_execute_with_result(self, test_manager):
        """Test execute_with_result method."""

        def _success_operation(session):
            new_record = TestModel(name='Result Test', status='active', value=700)
            session.add(new_record)
            return new_record

        success_result = test_manager.execute_with_result(_success_operation)
        assert success_result['success'] is True
        assert success_result['data'].name == 'Result Test'
        assert success_result['error'] is None

        def _failing_operation(session):
            raise RuntimeError('Test error')

        error_result = test_manager.execute_with_result(_failing_operation)
        assert error_result['success'] is False
        assert error_result['data'] is None
        assert 'Test error' in error_result['error']