# File: store_management/database/sqlalchemy/models/recipe.py
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from store_management.database.sqlalchemy.base import Base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean


class Recipe(Base):
    """
    Recipe model representing product manufacturing recipes.

    Attributes:
        id (int): Unique identifier for the recipe
        name (str): Name of the recipe
        description (str): Detailed description of the recipe
        product_id (int): Foreign key to the product this recipe creates
        estimated_production_time (float): Estimated time to produce
        notes (str): Additional notes about the recipe
        created_at (datetime): Timestamp of recipe creation
        updated_at (datetime): Timestamp of last update
    """
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    product_id = Column(Integer, ForeignKey('products.id'))
    estimated_production_time = Column(Float)  # in hours
    notes = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="recipes")
    items = relationship("RecipeItem", back_populates="recipe", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Recipe {self.name}>"


class RecipeItem(Base):
    """
    Individual items required for a recipe.

    Attributes:
        id (int): Unique identifier for the recipe item
        recipe_id (int): Foreign key to the parent recipe
        part_id (int): Foreign key to the part used in the recipe
        leather_id (int): Foreign key to the leather used in the recipe
        quantity (float): Quantity of the item needed
        is_optional (bool): Whether the item is optional in the recipe
        notes (str): Additional notes about the recipe item
    """
    __tablename__ = 'recipe_items'

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'))
    leather_id = Column(Integer, ForeignKey('leathers.id'))
    quantity = Column(Float, nullable=False)
    is_optional = Column(Boolean, default=False)
    notes = Column(String)

    # Relationships
    recipe = relationship("Recipe", back_populates="items")
    part = relationship("Part")
    leather = relationship("Leather")

    def __repr__(self):
        item_type = "Part" if self.part_id else "Leather"
        item_id = self.part_id or self.leather_id
        return f"<RecipeItem {self.id} - {item_type}: {item_id}, Qty: {self.quantity}>"