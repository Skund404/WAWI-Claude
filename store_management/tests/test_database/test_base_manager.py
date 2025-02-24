from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
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

        @inject(MaterialService)
        def get_by_name(self, name: str) ->List[TestModel]:
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
    clear_manager_cache()
    register_specialized_manager(TestModel, TestSpecializedManager)
    return get_manager(TestModel, session_factory)


class TestBaseManager:
    """
    Comprehensive test suite for BaseManager.
    """

        @inject(MaterialService)
        def test_create_single_record(self, test_manager):
        """
        Test creating a single record.
        """
        record = test_manager.create({'name': 'Test Record', 'value': 100})
        assert record is not None
        assert record.name == 'Test Record'
        assert record.value == 100
        assert record.id is not None

        @inject(MaterialService)
        def test_get_record(self, test_manager):
        """
        Test retrieving a single record by ID.
        """
        created_record = test_manager.create({'name': 'Retrieve Test',
            'value': 200})
        retrieved_record = test_manager.get(created_record.id)
        assert retrieved_record is not None
        assert retrieved_record.id == created_record.id
        assert retrieved_record.name == 'Retrieve Test'

        @inject(MaterialService)
        def test_update_record(self, test_manager):
        """
        Test updating an existing record.
        """
        record = test_manager.create({'name': 'Original Name', 'value': 300})
        updated_record = test_manager.update(record.id, {'name':
            'Updated Name', 'value': 400})
        assert updated_record is not None
        assert updated_record.name == 'Updated Name'
        assert updated_record.value == 400

        @inject(MaterialService)
        def test_delete_record(self, test_manager):
        """
        Test deleting a record.
        """
        record = test_manager.create({'name': 'Delete Test', 'value': 500})
        delete_result = test_manager.delete(record.id)
        assert delete_result is True
        retrieved_record = test_manager.get(record.id)
        assert retrieved_record is None

        @inject(MaterialService)
        def test_bulk_create(self, test_manager):
        """
        Test bulk creation of records.
        """
        records = test_manager.bulk_create([{'name': 'Bulk 1', 'value': 600
            }, {'name': 'Bulk 2', 'value': 700}, {'name': 'Bulk 3', 'value':
            800}])
        assert len(records) == 3
        assert all(record.id is not None for record in records)
        assert [record.name for record in records] == ['Bulk 1', 'Bulk 2',
            'Bulk 3']

        @inject(MaterialService)
        def test_bulk_update(self, test_manager):
        """
        Test bulk updating of records.
        """
        initial_records = test_manager.bulk_create([{'name': 'Update 1',
            'value': 900}, {'name': 'Update 2', 'value': 1000}])
        update_count = test_manager.bulk_update([{'id': initial_records[0].
            id, 'name': 'Updated 1', 'value': 1100}, {'id': initial_records
            [1].id, 'name': 'Updated 2', 'value': 1200}])
        assert update_count == 2
        updated_record1 = test_manager.get(initial_records[0].id)
        updated_record2 = test_manager.get(initial_records[1].id)
        assert updated_record1.name == 'Updated 1'
        assert updated_record1.value == 1100
        assert updated_record2.name == 'Updated 2'
        assert updated_record2.value == 1200

        @inject(MaterialService)
        def test_get_all(self, test_manager):
        """
        Test retrieving all records.
        """
        test_manager.bulk_create([{'name': 'Record 1', 'value': 1}, {'name':
            'Record 2', 'value': 2}, {'name': 'Record 3', 'value': 3}])
        all_records = test_manager.get_all()
        assert len(all_records) == 3

        @inject(MaterialService)
        def test_search(self, test_manager):
        """
        Test search functionality.
        """
        test_manager.bulk_create([{'name': 'Search Test 1', 'value': 2000},
            {'name': 'Search Test 2', 'value': 2100}, {'name':
            'Other Record', 'value': 2200}])
        search_results = test_manager.search('Search')
        assert len(search_results) == 2
        assert all('Search' in record.name for record in search_results)

        @inject(MaterialService)
        def test_filter(self, test_manager):
        """
        Test complex filtering.
        """
        test_manager.bulk_create([{'name': 'Filter 1', 'value': 3000}, {
            'name': 'Filter 2', 'value': 3100}, {'name': 'Filter 3',
            'value': 3200}])
        filtered_records = test_manager.filter_by_multiple({'name': 'Filter 1'}
            )
        assert len(filtered_records) == 1
        assert filtered_records[0].name == 'Filter 1'

        @inject(MaterialService)
        def test_exists(self, test_manager):
        """
        Test existence check.
        """
        test_manager.create({'name': 'Exists Test', 'value': 4000})
        exists_result = test_manager.exists(name='Exists Test')
        not_exists_result = test_manager.exists(name='Non-Existent')
        assert exists_result is True
        assert not_exists_result is False

        @inject(MaterialService)
        def test_count(self, test_manager):
        """
        Test record counting.
        """
        test_manager.bulk_create([{'name': 'Count 1', 'value': 5000}, {
            'name': 'Count 2', 'value': 5100}, {'name': 'Count 3', 'value':
            5200}])
        total_count = test_manager.count()
        filtered_count = test_manager.count(name='Count 1')
        assert total_count == 3
        assert filtered_count == 1

        @inject(MaterialService)
        def test_specialized_manager(self, session_factory):
        """
        Test specialized manager functionality.
        """
        specialized_manager = get_manager(TestModel, session_factory)
        specialized_manager.bulk_create([{'name': 'Special 1', 'value': 
            6000}, {'name': 'Special 2', 'value': 6100}, {'name':
            'Special 1', 'value': 6200}])
        special_records = specialized_manager.get_by_name('Special 1')
        assert len(special_records) == 2
        assert all(record.name == 'Special 1' for record in special_records)


class TestErrorHandling:
    """
    Test error handling scenarios.
    """

        @inject(MaterialService)
        def test_create_invalid_data(self, test_manager):
        """
        Test creating record with invalid data.
        """
        with pytest.raises(DatabaseError):
            test_manager.create({'non_existent_column': 'Invalid Data'})

        @inject(MaterialService)
        def test_update_non_existent_record(self, test_manager):
        """
        Test updating a non-existent record.
        """
        updated_record = test_manager.update(9999, {'name':
            'Non-Existent Update'})
        assert updated_record is None

        @inject(MaterialService)
        def test_delete_non_existent_record(self, test_manager):
        """
        Test deleting a non-existent record.
        """
        delete_result = test_manager.delete(9999)
        assert delete_result is False
