# Add these to your initialization code, perhaps in __init__.py
from utils.circular_import_resolver import register_lazy_import

register_lazy_import("database.models.transaction.InventoryTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["InventoryTransaction"]).InventoryTransaction)
register_lazy_import("database.models.transaction.HardwareTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["HardwareTransaction"]).HardwareTransaction)
register_lazy_import("database.models.transaction.LeatherTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["LeatherTransaction"]).LeatherTransaction)
register_lazy_import("database.models.transaction.MaterialTransaction",
                    lambda: __import__("database.models.transaction", fromlist=["MaterialTransaction"]).MaterialTransaction)