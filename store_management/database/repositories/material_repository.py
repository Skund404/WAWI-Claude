# Path: database/repositories/material_repository.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from database.models.material import Material, MaterialType, LeatherType, MaterialQualityGrade


class MaterialRepository:
    """
    Repository for managing materials with advanced querying capabilities.
    """

    def __init__(self, session: Session):
        self.session = session

    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material with comprehensive validation.

        Args:
            material_data (Dict[str, Any]): Material creation data

        Returns:
            Material: Created material instance
        """
        # Convert enum strings to actual enum values
        if 'material_type' in material_data:
            material_data['material_type'] = MaterialType[material_data['material_type']]

        if 'leather_type' in material_data:
            material_data['leather_type'] = LeatherType[material_data['leather_type']]

        if 'quality_grade' in material_data:
            material_data['quality_grade'] = MaterialQualityGrade[material_data['quality_grade']]

        material = Material(**material_data)
        self.session.add(material)
        self.session.commit()
        return material

    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        Retrieve a material by its ID.

        Args:
            material_id (int): Material identifier

        Returns:
            Optional[Material]: Retrieved material or None
        """
        return self.session.query(Material).filter(Material.id == material_id).first()

    def search_materials(
            self,
            material_type: Optional[MaterialType] = None,
            leather_type: Optional[LeatherType] = None,
            quality_grade: Optional[MaterialQualityGrade] = None,
            min_stock: Optional[float] = None,
            max_stock: Optional[float] = None
    ) -> List[Material]:
        """
        Advanced search for materials with multiple filtering options.

        Args:
            material_type (Optional[MaterialType]): Filter by material type
            leather_type (Optional[LeatherType]): Filter by leather type
            quality_grade (Optional[MaterialQualityGrade]): Filter by quality grade
            min_stock (Optional[float]): Minimum current stock
            max_stock (Optional[float]): Maximum current stock

        Returns:
            List[Material
# Path: database/repositories/material_repository.py (continued)

        Returns:
            List[Material]: Matching materials
        """
        query = self.session.query(Material)

        if material_type:
            query = query.filter(Material.material_type == material_type)

        if leather_type:
            query = query.filter(Material.leather_type == leather_type)

        if quality_grade:
            query = query.filter(Material.quality_grade == quality_grade)

        if min_stock is not None:
            query = query.filter(Material.current_stock >= min_stock)

        if max_stock is not None:
            query = query.filter(Material.current_stock <= max_stock)

        return query.all()

    def update_material(self, material_id: int, update_data: Dict[str, Any]) -> Optional[Material]:
        """
        Update an existing material.

        Args:
            material_id (int): Material identifier
            update_data (Dict[str, Any]): Data to update

        Returns:
            Optional[Material]: Updated material or None
        """
        material = self.get_material_by_id(material_id)

        if not material:
            return None

        # Convert enum strings to actual enum values
        if 'material_type' in update_data:
            update_data['material_type'] = MaterialType[update_data['material_type']]

        if 'leather_type' in update_data:
            update_data['leather_type'] = LeatherType[update_data['leather_type']]

        if 'quality_grade' in update_data:
            update_data['quality_grade'] = MaterialQualityGrade[update_data['quality_grade']]

        # Update material attributes
        for key, value in update_data.items():
            setattr(material, key, value)

        self.session.commit()
        return material

    def delete_material(self, material_id: int) -> bool:
        """
        Delete a material.

        Args:
            material_id (int): Material identifier

        Returns:
            bool: Success of deletion
        """
        material = self.get_material_by_id(material_id)

        if not material:
            return False

        try:
            self.session.delete(material)
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting material: {e}")
            return False

    def get_low_stock_materials(self, include_zero_stock: bool = False) -> List[Material]:
        """
        Retrieve materials with low stock.

        Args:
            include_zero_stock (bool): Whether to include materials with zero stock

        Returns:
            List[Material]: Materials below minimum stock level
        """
        query = self.session.query(Material)

        if not include_zero_stock:
            query = query.filter(Material.current_stock > 0)

        return query.filter(Material.current_stock <= Material.minimum_stock_level).all()

    def get_materials_by_supplier(self, supplier_id: int) -> List[Material]:
        """
        Retrieve materials from a specific supplier.

        Args:
            supplier_id (int): Supplier identifier

        Returns:
            List[Material]: Materials from the specified supplier
        """
        return self.session.query(Material).filter(Material.supplier_id == supplier_id).all()

    def generate_sustainability_report(self) -> List[Dict[str, Any]]:
        """
        Generate a sustainability report for materials.

        Returns:
            List[Dict[str, Any]]: Sustainability metrics for materials
        """
        sustainability_report = []

        for material in self.session.query(Material).all():
            sustainability_report.append({
                'material_id': material.id,
                'name': material.name,
                'material_type': material.material_type.name,
                'sustainability_score': material.calculate_sustainability_impact(),
                'ethical_sourcing_rating': material.ethical_sourcing_rating,
                'current_stock': material.current_stock
            })

        # Sort by sustainability score in descending order
        return sorted(
            sustainability_report,
            key=lambda x: x['sustainability_score'],
            reverse=True
        )