"""
File: database/models/recipe.py
Recipe model definitions.
Represents product recipes and their components.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from database.models.base import Base


class Recipe(Base):
    """
    Recipe model representing manufacturing instructions for products.
    """
    __tablename__ = 'recipes'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)
    labor_time = Column(Float, default=0.0)  # Time in minutes
    labor_cost = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    notes = Column(Text, nullable=True)
    version = Column(String(20), default="1.0")

    # Relationships - uncomment and adjust based on your actual relationships
    # product = relationship("Product", back_populates="recipe")
    # items = relationship("RecipeItem", back_populates="recipe", cascade="all, delete-orphan")

    def __repr__(self):
        """String representation of the Recipe model."""
        return f"<Recipe(id={self.id}, name='{self.name}', product_id={self.product_id})>"


class RecipeItem(Base):
    """
    RecipeItem model representing individual components in a recipe.
    """
    __tablename__ = 'recipe_items'
    __table_args__ = {'extend_existing': True}  # Add this to prevent duplicate table errors

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'), nullable=True)
    leather_id = Column(Integer, ForeignKey('leather.id'), nullable=True)
    quantity = Column(Float, default=1.0)
    area = Column(Float, nullable=True)  # For leather items
    position = Column(Integer, default=0)  # For ordering items
    notes = Column(Text, nullable=True)

    # Relationships - uncomment and adjust based on your actual relationships
    # recipe = relationship("Recipe", back_populates="items")
    # part = relationship("Part")
    # leather = relationship("Leather")

    def __repr__(self):
        """String representation of the RecipeItem model."""
        return f"<RecipeItem(id={self.id}, recipe_id={self.recipe_id}, part_id={self.part_id}, quantity={self.quantity})>"