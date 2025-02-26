# database/models/inventory.py

from sqlalchemy import Column, Date, Float, Integer, String

from database.models.base import Base, BaseModel

class Inventory(Base, BaseModel):
    """Represents an inventory item."""

    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<Inventory(id={self.id}, date='{self.date}', item_name='{self.item_name}', quantity={self.quantity}, unit_price={self.unit_price})>"