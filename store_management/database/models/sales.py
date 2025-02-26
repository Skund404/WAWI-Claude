# database/models/sales.py

from sqlalchemy import Column, Date, Float, Integer, String

from database.models.base import Base, BaseModel

class Sales(Base, BaseModel):
    """Represents a sales entry."""

    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<Sales(id={self.id}, date='{self.date}', item_name='{self.item_name}', quantity={self.quantity}, unit_price={self.unit_price})>"