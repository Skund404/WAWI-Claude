from database.sqlalchemy.managers.storage_manager import StorageManager

def test_storage_operations():
    manager = StorageManager(get_session)