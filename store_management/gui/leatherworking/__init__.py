# gui/leatherworking/__init__.py
"""
Initialization for leatherworking module with lazy import support.
"""

from utils.circular_import_resolver import register_lazy_import

# Lazy import for transactions and other potential circular dependencies
register_lazy_import(
    'InventoryTransaction',
    'database.models.transaction',
    'InventoryTransaction'
)

# You can add more lazy imports as needed
register_lazy_import(
    'MaterialTransaction',
    'database.models.transaction',
    'MaterialTransaction'
)

register_lazy_import(
    'LeatherTransaction',
    'database.models.transaction',
    'LeatherTransaction'
)

# Additional lazy import registrations can be added here