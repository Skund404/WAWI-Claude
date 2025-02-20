# File: store_management/database/sqlalchemy/model_utils.py
"""
Utility module for lazy loading of model classes to avoid circular imports.
"""


def get_model_classes():
    """
    Dynamically import and return a dictionary of model classes.

    Returns:
        Dict of model names to their corresponding classes
    """
    from . import models
    return {
        'Supplier': models.Supplier,
        'Order': models.Order,
        'OrderItem': models.OrderItem,
        'Part': models.Part,
        'Leather': models.Leather,
        'Recipe': models.Recipe,
        'RecipeItem': models.RecipeItem,
        'ShoppingList': models.ShoppingList,
        'ShoppingListItem': models.ShoppingListItem,
        'Shelf': models.Shelf,
        'InventoryTransaction': models.InventoryTransaction,
        'LeatherTransaction': models.LeatherTransaction,
        'ProductionOrder': models.ProductionOrder,
        'ProducedItem': models.ProducedItem
    }