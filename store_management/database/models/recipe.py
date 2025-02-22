# Path: database/models/recipe.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .base import BaseModel


class Recipe(BaseModel):
    """
    Represents a recipe in the inventory management system.

    Attributes:
        id (int): Unique identifier for the recipe
        name (str): Name of the recipe
        description (str): Detailed description of the recipe
        product_id (int): Foreign key to the product this recipe creates
        batch_size (float): Standard batch size for this recipe
        preparation_time (float): Estimated preparation time in minutes
        difficulty (str): Difficulty level of the recipe
        created_at (DateTime): Timestamp of recipe creation
        notes (str): Additional notes about the recipe

        product (relationship): Product created by this recipe
        items (relationship): Ingredients or components of the recipe
    """
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    batch_size = Column(Float, nullable=True, default=1.0)
    preparation_time = Column(Float, nullable=True)
    difficulty = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    # Relationships
    product = relationship('Product', back_populates='recipes')
    items = relationship('RecipeItem', back_populates='recipe',
                         cascade='all, delete-orphan')

    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}', batch_size={self.batch_size})>"

    def calculate_total_cost(self):
        """
        Calculate the total cost of the recipe based on its items.

        Returns:
            float: Total cost of the recipe
        """
        return sum(item.calculate_item_cost() for item in self.items)

    def check_ingredient_availability(self):
        """
        Check if all ingredients for the recipe are available.

        Returns:
            bool: True if all ingredients are available, False otherwise
        """
        return all(item.is_available() for item in self.items)


class RecipeItem(BaseModel):
    """
    Represents an individual item/ingredient in a recipe.

    Attributes:
        id (int): Unique identifier for the recipe item
        recipe_id (int): Foreign key to the parent recipe
        part_id (int): Foreign key to the inventory part
        leather_id (int): Foreign key to the leather material
        quantity (float): Quantity of the item required
        unit (str): Unit of measurement
        is_optional (bool): Whether the item is optional in the recipe

        recipe (relationship): Parent recipe
        part (relationship): Inventory part used in the recipe
        leather (relationship): Leather material used in the recipe
    """
    __tablename__ = 'recipe_items'

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(50), nullable=True)
    is_optional = Column(Integer, default=0)  # 0 for False, 1 for True

    # Relationships
    recipe = relationship('Recipe', back_populates='items')
    part = relationship('Part')
    leather = relationship('Leather')

    def __repr__(self):
        return f"<RecipeItem(id={self.id}, recipe_id={self.recipe_id}, quantity={self.quantity})>"

    def calculate_item_cost(self):
        """
        Calculate the cost of this recipe item based on its part or leather.

        Returns:
            float: Total cost of the item
        """
        if self.part:
            return (self.part.cost_price or 0) * self.quantity
        elif self.leather:
            return (self.leather.cost or 0) * self.quantity
        return 0.0

    def is_available(self):
        """
        Check if the item is available in sufficient quantity.

        Returns:
            bool: True if available, False otherwise
        """
        if self.is_optional:
            return True

        if self.part:
            return self.part.quantity >= self.quantity
        elif self.leather:
            return self.leather.available_area >= self.quantity

        return False