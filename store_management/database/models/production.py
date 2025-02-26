# database/models/production.py

from sqlalchemy import Column, Date, Float, Integer, String

from database.models.base import Base, BaseModel

class Production(Base, BaseModel):
    """Represents a production entry."""

    __tablename__ = "production"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    product_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)

    def __repr__(self) -> str:
        return f"<Production(id={self.id}, date='{self.date}', product_name='{self.product_name}', quantity={self.quantity}, unit_cost={self.unit_cost})>"