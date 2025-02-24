from di.core import inject
from services.interfaces import (
MaterialService,
ProjectService,
InventoryService,
OrderService,
)


def test_storage_operations():
    manager = StorageManager(get_session)
