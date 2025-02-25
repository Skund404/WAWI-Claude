# File: services/implementations.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional, Dict, Any

from database.models.material import Material, MaterialTransaction
from database.models.types import MaterialType, MaterialQualityGrade
from services.interfaces import MaterialService


class SQLAlchemyMaterialService(MaterialService):
    """
    SQLAlchemy implementation of the MaterialService interface.
    """

    def __init__(self, session: Session):
        """
        Initialize the service with a database session.

        Args:
            session (Session): SQLAlchemy database session
        """
        self._session = session

    def create_material(self, **kwargs) -> Material:
        """
        Create a new material entry.

        Args:
            **kwargs: Keyword arguments for material creation

        Returns:
            Material: Newly created material instance
        """
        material = Material(**kwargs)
        self._session.add(material)
        self._session.commit()
        return material

    def update_material(self, material_id: int, **kwargs) -> Material:
        """
        Update an existing material.

        Args:
            material_id (int): ID of the material to update
            **kwargs: Attributes to update

        Returns:
            Material: Updated material instance
        """
        material = self.get_material_by_id(material_id)
        if not material:
            raise ValueError(f"Material with ID {material_id} not found")

        for key, value in kwargs.items():
            setattr(material, key, value)

        self._session.commit()
        return material

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id (int): ID of the material to delete

        Returns:
            bool: True if deletion was successful
        """
        material = self.get_material_by_id(material_id)
        if not material:
            return False

        self._session.delete(material)
        self._session.commit()
        return True

    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        Retrieve a material by its ID.

        Args:
            material_id (int): ID of the material

        Returns:
            Optional[Material]: Material instance or None
        """
        return self._session.get(Material, material_id)

    def list_materials(self,
                       filter_params: Optional[Dict[str, Any]] = None,
                       page: int = 1,
                       per_page: int = 10) -> List[Material]:
        """
        List materials with optional filtering and pagination.

        Args:
            filter_params (dict, optional): Filtering parameters
            page (int): Page number for pagination
            per_page (int): Number of items per page

        Returns:
            List[Material]: List of material instances
        """
        query = self._session.query(Material)

        if filter_params:
            for key, value in filter_params.items():
                if hasattr(Material, key):
                    query = query.filter(getattr(Material, key) == value)

        query = query.offset((page - 1) * per_page).limit(per_page)
        return query.all()

    def update_stock(self,
                     material_id: int,
                     quantity_change: float,
                     transaction_type: str = 'ADJUSTMENT') -> Material:
        """
        Update stock for a specific material.

        Args:
            material_id (int): ID of the material
            quantity_change (float): Amount to change stock
            transaction_type (str): Type of stock transaction

        Returns:
            Material: Updated material instance
        """
        material = self.get_material_by_id(material_id)
        if not material:
            raise ValueError(f"Material with ID {material_id} not found")

        new_stock = material.current_stock + quantity_change
        if new_stock < 0:
            raise ValueError(
                f'Stock cannot become negative. Current: '
                f'{material.current_stock}, Change: {quantity_change}'
            )

        material.current_stock = new_stock

        # Create a transaction record
        transaction = MaterialTransaction(
            material_id=material_id,
            quantity_change=quantity_change,
            transaction_type=transaction_type
        )
        self._session.add(transaction)

        self._session.commit()
        return material