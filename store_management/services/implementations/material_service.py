

from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
class MaterialService(BaseService[Material], IMaterialService):
    """
    Service implementation for managing materials.

    Provides business logic and validation for material-related operations.
    """

        @inject(MaterialService)
        def __init__(self, repository: MaterialRepository, unit_of_work:
        Optional[IUnitOfWork]=None):
        """
        Initialize the MaterialService.

        Args:
            repository (MaterialRepository): Repository for material data access
            unit_of_work (Optional[IUnitOfWork], optional): Unit of work for transactions
        """
        super().__init__(repository, unit_of_work)
        self._repository = repository

        @inject(MaterialService)
        def _validate_create_data(self, data: Dict[str, Any]) ->None:
        """
        Validate data before creating a new material.

        Args:
            data (Dict[str, Any]): Material creation data

        Raises:
            ValidationError: If data is invalid
        """
        if not data.get('name'):
            raise ValidationError('Material name is required', {'name':
                'Name cannot be empty'})
        try:
            material_type = MaterialType(data.get('material_type'))
        except ValueError:
            raise ValidationError('Invalid material type', {'material_type':
                'Must be a valid MaterialType'})
        try:
            quality_grade = MaterialQualityGrade(data.get('quality_grade'))
        except ValueError:
            raise ValidationError('Invalid quality grade', {'quality_grade':
                'Must be a valid MaterialQualityGrade'})
        stock = data.get('stock', 0)
        if not isinstance(stock, (int, float)) or stock < 0:
            raise ValidationError('Invalid stock quantity', {'stock':
                'Stock must be a non-negative number'})
        unit_price = data.get('unit_price', 0)
        if not isinstance(unit_price, (int, float)) or unit_price < 0:
            raise ValidationError('Invalid unit price', {'unit_price':
                'Unit price must be a non-negative number'})

        @inject(MaterialService)
        def _validate_update_data(self, existing_entity: Material, update_data:
        Dict[str, Any]) ->None:
        """
        Validate data before updating an existing material.

        Args:
            existing_entity (Material): The existing material
            update_data (Dict[str, Any]): Material update data

        Raises:
            ValidationError: If update data is invalid
        """
        if 'name' in update_data and not update_data['name']:
            raise ValidationError('Material name cannot be empty', {'name':
                'Name cannot be empty'})
        if 'material_type' in update_data:
            try:
                MaterialType(update_data['material_type'])
            except ValueError:
                raise ValidationError('Invalid material type', {
                    'material_type': 'Must be a valid MaterialType'})
        if 'quality_grade' in update_data:
            try:
                MaterialQualityGrade(update_data['quality_grade'])
            except ValueError:
                raise ValidationError('Invalid quality grade', {
                    'quality_grade': 'Must be a valid MaterialQualityGrade'})
        if 'stock' in update_data:
            stock = update_data['stock']
            if not isinstance(stock, (int, float)) or stock < 0:
                raise ValidationError('Invalid stock quantity', {'stock':
                    'Stock must be a non-negative number'})
        if 'unit_price' in update_data:
            unit_price = update_data['unit_price']
            if not isinstance(unit_price, (int, float)) or unit_price < 0:
                raise ValidationError('Invalid unit price', {'unit_price':
                    'Unit price must be a non-negative number'})

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
            ValidationError: If stock update is invalid
        """
        try:
            material = self.get_by_id(material_id)
            if not isinstance(quantity_change, (int, float)):
                raise ValidationError('Invalid quantity change', {
                    'quantity_change': 'Must be a number'})
            if hasattr(self._repository, 'update_stock'):
                return self._repository.update_stock(material_id,
                    quantity_change, transaction_type, notes)
            else:
                material.update_stock(quantity_change)
                return self.update(material_id, {'stock': material.stock})
        except (NotFoundError, ValidationError):
            raise
        except Exception as e:
            self._logger.error(
                f'Error updating stock for material {material_id}: {e}')
            raise ApplicationError(f'Failed to update material stock: {str(e)}'
                , {'material_id': material_id, 'quantity_change':
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
            if hasattr(self._repository, 'get_low_stock_materials'):
                return self._repository.get_low_stock_materials(
                    include_zero_stock)
            all_materials = self.get_all()
            return [material for material in all_materials if material.
                is_low_stock() or include_zero_stock and material.stock == 0]
        except Exception as e:
            self._logger.error(f'Error retrieving low stock materials: {e}')
            raise ApplicationError(
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
            if hasattr(self._repository, 'search_materials'):
                return self._repository.search_materials(search_params)
            all_materials = self.get_all()
            return [material for material in all_materials if all(self.
                _match_search_criterion(material, key, value) for key,
                value in search_params.items())]
        except Exception as e:
            self._logger.error(f'Error searching materials: {e}')
            raise ApplicationError(f'Failed to search materials: {str(e)}',
                {'search_params': search_params})

        @inject(MaterialService)
        def _match_search_criterion(self, material: Material, key: str, value: Any
        ) ->bool:
        """
        Helper method to match a single search criterion.

        Args:
            material (Material): Material to check
            key (str): Search key
            value (Any): Search value

        Returns:
            bool: True if the material matches the criterion, False otherwise
        """
        try:
            if key == 'material_type':
                return material.material_type.value == value
            elif key == 'quality_grade':
                return material.quality_grade.value == value
            attr_value = getattr(material, key, None)
            if isinstance(attr_value, str) and isinstance(value, str):
                return value.lower() in attr_value.lower()
            return attr_value == value
        except Exception:
            return False

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
            if hasattr(self._repository, 'generate_material_usage_report'):
                return self._repository.generate_material_usage_report(
                    start_date, end_date)
            materials = self.get_all()
            report = {'total_materials': len(materials),
                'low_stock_materials': 0, 'materials': []}
            for material in materials:
                material_data = material.to_dict()
                if material.is_low_stock():
                    report['low_stock_materials'] += 1
                report['materials'].append(material_data)
            return report
        except Exception as e:
            self._logger.error(f'Error generating material usage report: {e}')
            raise ApplicationError(
                f'Failed to generate material usage report: {str(e)}', {
                'start_date': start_date, 'end_date': end_date})

        @inject(MaterialService)
        def deactivate_material(self, material_id: Any) ->Material:
        """
        Deactivate a material, preventing further use.

        Args:
            material_id (Any): ID of the material to deactivate

        Returns:
            Material: The deactivated material
        """
        try:
            material = self.get_by_id(material_id)
            return self.update(material_id, {'is_active': False})
        except Exception as e:
            self._logger.error(
                f'Error deactivating material {material_id}: {e}')
            raise ApplicationError(f'Failed to deactivate material: {str(e)}',
                {'material_id': material_id})

        @inject(MaterialService)
        def activate_material(self, material_id: Any) ->Material:
        """
        Reactivate a previously deactivated material.

        Args:
            material_id (Any): ID of the material to activate

        Returns:
            Material: The activated material
        """
        try:
            material = self.get_by_id(material_id)
            return self.update(material_id, {'is_active': True})
        except Exception as e:
            self._logger.error(f'Error activating material {material_id}: {e}')
            raise ApplicationError(f'Failed to activate material: {str(e)}',
                {'material_id': material_id})

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

        Raises:
            NotFoundError: If either material is not found
        """
        try:
            original_material = self.get_by_id(original_material_id)
            substitute_material = self.get_by_id(substitute_material_id)
            substitution_checks = [original_material.material_type ==
                substitute_material.material_type, substitute_material.
                stock > 0, substitute_material.quality_grade.value >=
                original_material.quality_grade.value]
            if hasattr(self._repository, 'validate_material_substitution'):
                repo_check = self._repository.validate_material_substitution(
                    original_material_id, substitute_material_id)
                substitution_checks.append(repo_check)
            return all(substitution_checks)
        except NotFoundError:
            raise
        except Exception as e:
            self._logger.error(
                f'Error validating material substitution ({original_material_id} -> {substitute_material_id}): {e}'
                )
            raise ApplicationError(
                f'Failed to validate material substitution: {str(e)}', {
                'original_material_id': original_material_id,
                'substitute_material_id': substitute_material_id})
