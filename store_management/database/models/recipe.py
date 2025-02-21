# store_management/database/models/recipe.py

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Recipe(Base):
    """Recipe model for manufacturing products"""
    __tablename__ = 'recipes'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    product_id = Column(Integer, ForeignKey('products.id'))
    labor_minutes = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    product = relationship("Product", back_populates="recipes")
    items = relationship("RecipeItem", back_populates="recipe", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Recipe(id={self.id}, name='{self.name}')>"


class RecipeItem(Base):
    """Items required for a recipe"""
    __tablename__ = 'recipe_items'

    id = Column(Integer, primary_key=True)
    recipe_id = Column(Integer, ForeignKey('recipes.id'), nullable=False)
    part_id = Column(Integer, ForeignKey('parts.id'))
    leather_id = Column(Integer, ForeignKey('leathers.id'))
    quantity = Column(Float, default=1.0)
    area = Column(Float)  # For leather items (square feet)
    notes = Column(String)

    # Relationships - only reference one of part or leather
    recipe = relationship("Recipe", back_populates="items")
    part = relationship("Part", back_populates="recipe_items")
    leather = relationship("Leather", back_populates="recipe_items")

    def __repr__(self):
        return f"<RecipeItem(id={self.id}, recipe_id={self.recipe_id})>"