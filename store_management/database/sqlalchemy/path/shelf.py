# database\sqlalchemy\models\shelf.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class Shelf(Base):
    __tablename__ = 'shelves'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    location = Column(String)
    description = Column(String)

    leather_items = relationship("LeatherItem", back_populates="shelf")

    def __repr__(self):
        return f"<Shelf {self.name}>"