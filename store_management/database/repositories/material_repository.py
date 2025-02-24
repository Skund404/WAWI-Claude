

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class MaterialRepository(BaseRepository[Material], IMaterialRepository):
    """
    SQLAlchemy implementation of the Material Repository.

    Provides data access and manipulation methods for materials.
    """

        @inject(MaterialService)
        def __init__(self, session: Session):
        """
        Initialize the Material Repository.

        Args:
            session (Session): SQLAlchemy database session
        """
        super().__init__(session, Material)
        self._session = session

        @inject(MaterialService)
        def update_stock(self, material_id: Any, quantity_change: float,
        transaction_type: str, notes: Optional[str]=None) ->Material:
        """
        Update the stock of a material.

        Args:
            material_id (Any): ID of the material
            quantity_change (float): Quantity to add or subtract
            transaction_type (str): Type of stock transaction
            notes (Optional[str], optional): Additional notes for the transaction

        Returns:
            Material: Updated material

        Raises:
            NotFoundError: If material is not found
            ValidationError: If stock update would be invalid
        """
        try:
            material = self.get_by_id(material_id)
            new_stock = material.stock + quantity_change
            if new_stock < 0:
                raise ValidationError('Insufficient stock', {
                    'current_stock': material.stock, 'quantity_change':
                    quantity_change})
            material.stock = new_stock
            self._session.commit()
            return material
        except ValidationError:
            self._session.rollback()
            raise
        except Exception as e:
            self._session.rollback()
            raise DatabaseError(f'Failed to update material stock: {str(e)}',
                {'material_id': material_id, 'quantity_change':
                quantity_change})

        @inject(MaterialService)
        def get_low_stock_materials(self, include_zero_stock: bool=False) ->List[
        Material]:
        """
        Retrieve materials with low stock.

        Args:
            include_zero_stock (bool, optional): Whether to include materials
                with zero stock. Defaults to False.

        Returns:
            List[Material]: List of low stock materials
        """
        try:
            query = self._session.query(Material)
            if include_zero_stock:
                query = query.filter(Material.stock <= Material.minimum_stock)
            else:
                query = query.filter((Material.stock <= Material.
                    minimum_stock) & (Material.stock > 0))
            return query.all()
        except Exception as e:
            raise DatabaseError(
                f'Failed to retrieve low stock materials: {str(e)}', {
                'include_zero_stock': include_zero_stock})

        @inject(MaterialService)
        def search_materials(self, search_params: Dict[str, Any]) ->List[Material]:
        """
        Search materials based on multiple criteria.

        Args:
            search_params (Dict[str, Any]): Search criteria

        Returns:
            List[Material]: List of matching materials
        """
        try:
            query = self._session.query(Material)
            for key, value in search_params.items():
                if key == 'material_type':
                    query = query.filter(Material.material_type ==
                        MaterialType(value))
                elif key == 'quality_grade':
                    query = query.filter(Material.quality_grade ==
                        MaterialQualityGrade(value))
                elif key == 'name':
                    query = query.filter(func.lower(Material.name).like(
                        f'%{value.lower()}%'))
                else:
                    query = query.filter(getattr(Material, key) == value)
            return query.all()
        except Exception as e:
            raise DatabaseError(f'Failed to search materials: {str(e)}', {
                'search_params': search_params})

        @inject(MaterialService)
        def generate_material_usage_report(self, start_date: Optional[str]=None,
        end_date: Optional[str]=None) ->Dict[str, Any]:
        """
        Generate a comprehensive material usage report.

        Args:
            start_date (Optional[str], optional): Start date for the report
            end_date (Optional[str], optional): End date for the report

        Returns:
            Dict[str, Any]: Material usage report
        """
        try:
            materials = self._session.query(Material).all()
            report = {'total_materials': len(materials),
                'low_stock_materials': 0, 'materials': []}
            for material in materials:
                material_data = {'id': material.id, 'name': material.name,
                    'material_type': material.material_type.value,
                    'quality_grade': material.quality_grade.value,
                    'current_stock': material.stock, 'minimum_stock':
                    material.minimum_stock, 'is_low_stock': material.stock <=
                    material.minimum_stock}
                if material_data['is_low_stock']:
                    report['low_stock_materials'] += 1
                report['materials'].append(material_data)
            return report
        except Exception as e:
            raise DatabaseError(
                f'Failed to generate material usage report: {str(e)}', {
                'start_date': start_date, 'end_date': end_date})

        @inject(MaterialService)
        def validate_material_substitution(self, original_material_id: Any,
        substitute_material_id: Any) ->bool:
        """
        Check if one material can be substituted for another.

        Args:
            original_material_id (Any): ID of the original material
            substitute_material_id (Any): ID of the potential substitute material

        Returns:
            bool: True if substitution is possible, False otherwise
        """
        try:
            original_material = self.get_by_id(original_material_id)
            substitute_material = self.get_by_id(substitute_material_id)
            criteria = [original_material.material_type ==
                substitute_material.material_type, substitute_material.
                stock > 0, substitute_material.quality_grade.value >=
                original_material.quality_grade.value]
            return all(criteria)
        except Exception as e:
            raise DatabaseError(
                f'Failed to validate material substitution: {str(e)}', {
                'original_material_id': original_material_id,
                'substitute_material_id': substitute_material_id})
