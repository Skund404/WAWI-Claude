# services/implementations/material_service.py
"""
Implementation of the material service interface.
Provides business logic for material management in the leatherworking application.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from database.models.enums import (
    InventoryStatus, MaterialType, LeatherType, HardwareType,
    TransactionType, QualityGrade
)
from database.models.material import Material, Leather, Hardware
from database.models.base import ModelValidationError
from database.exceptions import ModelNotFoundError, RepositoryError
from database.repositories.repository_factory import RepositoryFactory
from services.interfaces.material_service import IMaterialService
from services.base_service import BaseService, ServiceError, NotFoundError, ValidationError
from utils.logger import get_logger
from di.core import inject

logger = get_logger(__name__)


class MaterialService(BaseService, IMaterialService):
    """
    Implementation of the material service interface.

    Provides business logic for material management in the leatherworking application.
    """

    @inject
    def __init__(self, repository_factory: RepositoryFactory):
        """
        Initialize the material service.

        Args:
            repository_factory: Factory for creating repositories
        """
        super().__init__()
        self._repository_factory = repository_factory
        self._leather_repository = repository_factory.get_leather_repository()
        self._hardware_repository = repository_factory.get_hardware_repository()
        self._supplies_repository = repository_factory.get_supplies_repository()
        self._material_repository = repository_factory.get_material_repository()
        logger.debug("Initialized MaterialService")

    def get_all_materials(self,
                          include_deleted: bool = False,
                          status: Optional[InventoryStatus] = None,
                          material_type: Optional[MaterialType] = None) -> List[Material]:
        """
        Get all materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted materials
            status: Filter by inventory status
            material_type: Filter by material type

        Returns:
            List of material objects
        """
        try:
            # Use general material repository for all materials
            return self._material_repository.get_all_materials(
                include_deleted=include_deleted,
                status=status,
                material_type=material_type
            )
        except RepositoryError as e:
            logger.error(f"Error getting materials: {str(e)}")
            raise ServiceError(f"Failed to get materials: {str(e)}")

    def get_material_by_id(self, material_id: int) -> Optional[Material]:
        """
        Get material by ID.

        Args:
            material_id: ID of the material

        Returns:
            Material object or None if not found
        """
        try:
            # Get material from the appropriate repository based on type
            material = self._material_repository.get_material_with_inventory(material_id)

            if not material:
                return None

            # Return the material
            return material

        except RepositoryError as e:
            logger.error(f"Error getting material by ID {material_id}: {str(e)}")
            raise ServiceError(f"Failed to get material: {str(e)}")

    def create_material(self, material_data: Dict[str, Any]) -> Material:
        """
        Create a new material.

        Args:
            material_data: Material data dictionary

        Returns:
            Created material object
        """
        try:
            # Determine material type and use appropriate repository
            material_type = material_data.get('material_type')

            if not material_type:
                raise ValidationError("Material type is required")

            # Route to appropriate repository based on material type
            if material_type == MaterialType.LEATHER.value:
                return self._create_leather(material_data)
            elif material_type == MaterialType.HARDWARE.value:
                return self._create_hardware(material_data)
            elif material_type in [t.value for t in self._supplies_repository.SUPPLY_MATERIAL_TYPES]:
                return self._create_supply(material_data)
            else:
                # Use general material repository for other types
                return self._material_repository.create_material(material_data)

        except ModelValidationError as e:
            logger.error(f"Validation error creating material: {str(e)}")
            raise ValidationError(str(e))
        except RepositoryError as e:
            logger.error(f"Error creating material: {str(e)}")
            raise ServiceError(f"Failed to create material: {str(e)}")

    def _create_leather(self, leather_data: Dict[str, Any]) -> Leather:
        """Create a new leather material."""
        try:
            # Use leather repository for leather-specific creation
            leather = self._leather_repository.create(leather_data)
            logger.info(f"Created new leather material: {leather.name} (ID: {leather.id})")
            return leather
        except ModelValidationError as e:
            raise ValidationError(str(e))
        except RepositoryError as e:
            raise ServiceError(f"Failed to create leather material: {str(e)}")

    def _create_hardware(self, hardware_data: Dict[str, Any]) -> Hardware:
        """Create a new hardware material."""
        try:
            # Use hardware repository for hardware-specific creation
            hardware = self._hardware_repository.create(hardware_data)
            logger.info(f"Created new hardware material: {hardware.name} (ID: {hardware.id})")
            return hardware
        except ModelValidationError as e:
            raise ValidationError(str(e))
        except RepositoryError as e:
            raise ServiceError(f"Failed to create hardware material: {str(e)}")

    def _create_supply(self, supply_data: Dict[str, Any]) -> Material:
        """Create a new supply material."""
        try:
            # Use supplies repository for supply-specific creation
            supply = self._supplies_repository.create_supply(supply_data)
            logger.info(f"Created new supply material: {supply.name} (ID: {supply.id})")
            return supply
        except ModelValidationError as e:
            raise ValidationError(str(e))
        except RepositoryError as e:
            raise ServiceError(f"Failed to create supply material: {str(e)}")

    def update_material(self, material_id: int, update_data: Dict[str, Any]) -> Material:
        """
        Update existing material.

        Args:
            material_id: ID of the material
            update_data: Updated material data

        Returns:
            Updated material object
        """
        try:
            # Get the material to determine its type
            material = self.get_material_by_id(material_id)

            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Route to appropriate repository based on material type
            if material.material_type == MaterialType.LEATHER.value:
                return self._update_leather(material_id, update_data)
            elif material.material_type == MaterialType.HARDWARE.value:
                return self._update_hardware(material_id, update_data)
            elif material.material_type in [t.value for t in self._supplies_repository.SUPPLY_MATERIAL_TYPES]:
                return self._update_supply(material_id, update_data)
            else:
                # Use general material repository for other types
                return self._material_repository.batch_update([{**update_data, 'id': material_id}])[0]

        except ModelValidationError as e:
            logger.error(f"Validation error updating material {material_id}: {str(e)}")
            raise ValidationError(str(e))
        except ModelNotFoundError as e:
            logger.error(f"Material {material_id} not found: {str(e)}")
            raise NotFoundError(str(e))
        except RepositoryError as e:
            logger.error(f"Error updating material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to update material: {str(e)}")

    def _update_leather(self, leather_id: int, update_data: Dict[str, Any]) -> Leather:
        """Update an existing leather material."""
        try:
            leathers = self._leather_repository.batch_update([{**update_data, 'id': leather_id}])
            if not leathers:
                raise NotFoundError(f"Leather with ID {leather_id} not found")

            logger.info(f"Updated leather material: {leathers[0].name} (ID: {leather_id})")
            return leathers[0]
        except ModelValidationError as e:
            raise ValidationError(str(e))
        except ModelNotFoundError as e:
            raise NotFoundError(str(e))
        except RepositoryError as e:
            raise ServiceError(f"Failed to update leather material: {str(e)}")

    def _update_hardware(self, hardware_id: int, update_data: Dict[str, Any]) -> Hardware:
        """Update an existing hardware material."""
        try:
            hardware_items = self._hardware_repository.batch_update([{**update_data, 'id': hardware_id}])
            if not hardware_items:
                raise NotFoundError(f"Hardware with ID {hardware_id} not found")

            logger.info(f"Updated hardware material: {hardware_items[0].name} (ID: {hardware_id})")
            return hardware_items[0]
        except ModelValidationError as e:
            raise ValidationError(str(e))
        except ModelNotFoundError as e:
            raise NotFoundError(str(e))
        except RepositoryError as e:
            raise ServiceError(f"Failed to update hardware material: {str(e)}")

    def _update_supply(self, supply_id: int, update_data: Dict[str, Any]) -> Material:
        """Update an existing supply material."""
        try:
            supplies = self._supplies_repository.batch_update([{**update_data, 'id': supply_id}])
            if not supplies:
                raise NotFoundError(f"Supply with ID {supply_id} not found")

            logger.info(f"Updated supply material: {supplies[0].name} (ID: {supply_id})")
            return supplies[0]
        except ModelValidationError as e:
            raise ValidationError(str(e))
        except ModelNotFoundError as e:
            raise NotFoundError(str(e))
        except RepositoryError as e:
            raise ServiceError(f"Failed to update supply material: {str(e)}")

    def delete_material(self, material_id: int) -> bool:
        """
        Soft delete a material.

        Args:
            material_id: ID of the material

        Returns:
            Success status
        """
        try:
            # Get the material to determine its type
            material = self.get_material_by_id(material_id)

            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Soft delete by updating is_deleted flag
            update_data = {'is_deleted': True}

            # Route to appropriate repository based on material type
            if material.material_type == MaterialType.LEATHER.value:
                self._update_leather(material_id, update_data)
            elif material.material_type == MaterialType.HARDWARE.value:
                self._update_hardware(material_id, update_data)
            elif material.material_type in [t.value for t in self._supplies_repository.SUPPLY_MATERIAL_TYPES]:
                self._update_supply(material_id, update_data)
            else:
                # Use general material repository for other types
                self._material_repository.batch_update([{**update_data, 'id': material_id}])

            logger.info(f"Soft deleted material ID {material_id}")
            return True

        except NotFoundError:
            # Re-raise not found errors
            raise
        except Exception as e:
            logger.error(f"Error deleting material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to delete material: {str(e)}")

    def search_materials(self, search_term: str) -> List[Material]:
        """
        Search for materials matching a search term.

        Args:
            search_term: Text to search for

        Returns:
            List of matching materials
        """
        try:
            # Search in all material repositories
            leather_results = self._leather_repository.search_leathers(search_term)
            hardware_results = self._hardware_repository.search_hardware(search_term)
            supplies_results = self._supplies_repository.search_supplies(search_term)

            # Combine results
            all_results = leather_results + hardware_results + supplies_results

            logger.debug(f"Search for '{search_term}' returned {len(all_results)} materials")
            return all_results

        except RepositoryError as e:
            logger.error(f"Error searching materials: {str(e)}")
            raise ServiceError(f"Failed to search materials: {str(e)}")

    def update_inventory_quantity(self,
                                  material_id: int,
                                  quantity_change: float,
                                  transaction_type: TransactionType,
                                  notes: Optional[str] = None) -> bool:
        """
        Update material inventory quantity.

        Args:
            material_id: ID of the material
            quantity_change: Amount to adjust (positive or negative)
            transaction_type: Type of transaction
            notes: Optional notes about the transaction

        Returns:
            Success status
        """
        try:
            # Get the material to determine its type
            material = self.get_material_by_id(material_id)

            if not material:
                raise NotFoundError(f"Material with ID {material_id} not found")

            # Route to appropriate repository based on material type
            if material.material_type == MaterialType.LEATHER.value:
                self._leather_repository.update_inventory_quantity(
                    material_id, quantity_change, transaction_type, notes=notes
                )
            elif material.material_type == MaterialType.HARDWARE.value:
                self._hardware_repository.update_inventory_quantity(
                    material_id, quantity_change, transaction_type, notes=notes
                )
            elif material.material_type in [t.value for t in self._supplies_repository.SUPPLY_MATERIAL_TYPES]:
                self._supplies_repository.update_inventory_quantity(
                    material_id, quantity_change, transaction_type, notes=notes
                )
            else:
                # Use material repository for other types
                self._material_repository.update_inventory_quantity(
                    material_id, quantity_change, transaction_type, notes=notes
                )

            logger.info(f"Updated inventory for material ID {material_id}: {quantity_change} units")
            return True

        except ModelValidationError as e:
            logger.error(f"Validation error updating inventory for material {material_id}: {str(e)}")
            raise ValidationError(str(e))
        except ModelNotFoundError as e:
            logger.error(f"Material {material_id} or inventory not found: {str(e)}")
            raise NotFoundError(str(e))
        except RepositoryError as e:
            logger.error(f"Error updating inventory for material {material_id}: {str(e)}")
            raise ServiceError(f"Failed to update inventory: {str(e)}")

    # Leather-specific methods
    def get_all_leathers(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         leather_type: Optional[LeatherType] = None,
                         quality: Optional[QualityGrade] = None) -> List[Leather]:
        """
        Get all leather materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted leathers
            status: Filter by inventory status
            leather_type: Filter by leather type
            quality: Filter by quality grade

        Returns:
            List of leather objects
        """
        try:
            return self._leather_repository.get_all_leathers(
                include_deleted=include_deleted,
                status=status,
                leather_type=leather_type,
                quality=quality
            )
        except RepositoryError as e:
            logger.error(f"Error getting leathers: {str(e)}")
            raise ServiceError(f"Failed to get leathers: {str(e)}")

    def get_leather_by_id(self, leather_id: int) -> Optional[Leather]:
        """
        Get leather by ID.

        Args:
            leather_id: ID of the leather

        Returns:
            Leather object or None if not found
        """
        try:
            return self._leather_repository.get_leather_with_inventory(leather_id)
        except RepositoryError as e:
            logger.error(f"Error getting leather by ID {leather_id}: {str(e)}")
            raise ServiceError(f"Failed to get leather: {str(e)}")

    # Hardware-specific methods
    def get_all_hardware(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         hardware_type: Optional[HardwareType] = None) -> List[Hardware]:
        """
        Get all hardware materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted hardware
            status: Filter by inventory status
            hardware_type: Filter by hardware type

        Returns:
            List of hardware objects
        """
        try:
            return self._hardware_repository.get_all_hardware(
                include_deleted=include_deleted,
                status=status,
                hardware_type=hardware_type
            )
        except RepositoryError as e:
            logger.error(f"Error getting hardware: {str(e)}")
            raise ServiceError(f"Failed to get hardware: {str(e)}")

    def get_hardware_by_id(self, hardware_id: int) -> Optional[Hardware]:
        """
        Get hardware by ID.

        Args:
            hardware_id: ID of the hardware

        Returns:
            Hardware object or None if not found
        """
        try:
            return self._hardware_repository.get_hardware_with_inventory(hardware_id)
        except RepositoryError as e:
            logger.error(f"Error getting hardware by ID {hardware_id}: {str(e)}")
            raise ServiceError(f"Failed to get hardware: {str(e)}")

    # Supplies-specific methods
    def get_all_supplies(self,
                         include_deleted: bool = False,
                         status: Optional[InventoryStatus] = None,
                         material_type: Optional[MaterialType] = None) -> List[Material]:
        """
        Get all supply materials with optional filtering.

        Args:
            include_deleted: Whether to include soft-deleted supplies
            status: Filter by inventory status
            material_type: Filter by specific material type

        Returns:
            List of supply objects
        """
        try:
            return self._supplies_repository.get_all_supplies(
                include_deleted=include_deleted,
                status=status,
                material_type=material_type
            )
        except RepositoryError as e:
            logger.error(f"Error getting supplies: {str(e)}")
            raise ServiceError(f"Failed to get supplies: {str(e)}")

    def get_supply_by_id(self, supply_id: int) -> Optional[Material]:
        """
        Get supply by ID.

        Args:
            supply_id: ID of the supply

        Returns:
            Supply object or None if not found
        """
        try:
            return self._supplies_repository.get_supply_with_inventory(supply_id)
        except RepositoryError as e:
            logger.error(f"Error getting supply by ID {supply_id}: {str(e)}")
            raise ServiceError(f"Failed to get supply: {str(e)}")

    def get_supplies_by_type(self, material_type: MaterialType) -> List[Material]:
        """
        Get supplies by material type.

        Args:
            material_type: Type of material to filter by

        Returns:
            List of supply objects matching the type
        """
        try:
            # Check if the material type is valid for supplies
            if material_type not in self._supplies_repository.SUPPLY_MATERIAL_TYPES:
                logger.warning(f"Material type {material_type} is not a valid supply type")
                return []

            return self._supplies_repository.get_supplies_by_material_type(material_type)
        except RepositoryError as e:
            logger.error(f"Error getting supplies by type {material_type}: {str(e)}")
            raise ServiceError(f"Failed to get supplies by type: {str(e)}")

    # Inventory statistics methods
    def get_low_stock_materials(self) -> Dict[str, List[Material]]:
        """
        Get all materials with low stock, grouped by category.

        Returns:
            Dictionary of low stock materials by category
            (leather, hardware, supplies)
        """
        try:
            # Get low stock materials from each repository
            low_stock_leathers = self._leather_repository.get_low_stock_leathers()
            low_stock_hardware = self._hardware_repository.get_low_stock_hardware()
            low_stock_supplies = self._supplies_repository.get_low_stock_supplies()

            # Group results
            result = {
                "leather": low_stock_leathers,
                "hardware": low_stock_hardware,
                "supplies": low_stock_supplies
            }

            logger.debug(
                f"Found low stock materials: {len(low_stock_leathers)} leathers, "
                f"{len(low_stock_hardware)} hardware items, {len(low_stock_supplies)} supplies"
            )
            return result

        except RepositoryError as e:
            logger.error(f"Error getting low stock materials: {str(e)}")
            raise ServiceError(f"Failed to get low stock materials: {str(e)}")

    def get_out_of_stock_materials(self) -> Dict[str, List[Material]]:
        """
        Get all materials that are out of stock, grouped by category.

        Returns:
            Dictionary of out of stock materials by category
            (leather, hardware, supplies)
        """
        try:
            # Get out of stock materials from each repository
            out_of_stock_leathers = self._leather_repository.get_out_of_stock_leathers()
            out_of_stock_hardware = self._hardware_repository.get_out_of_stock_hardware()
            out_of_stock_supplies = self._supplies_repository.get_out_of_stock_supplies()

            # Group results
            result = {
                "leather": out_of_stock_leathers,
                "hardware": out_of_stock_hardware,
                "supplies": out_of_stock_supplies
            }

            logger.debug(
                f"Found out of stock materials: {len(out_of_stock_leathers)} leathers, "
                f"{len(out_of_stock_hardware)} hardware items, {len(out_of_stock_supplies)} supplies"
            )
            return result

        except RepositoryError as e:
            logger.error(f"Error getting out of stock materials: {str(e)}")
            raise ServiceError(f"Failed to get out of stock materials: {str(e)}")

    def get_inventory_value_report(self) -> Dict[str, Any]:
        """
        Get comprehensive inventory value report.

        Returns:
            Dictionary with inventory value statistics
        """
        try:
            # Get inventory values from each repository
            leather_value = self._leather_repository.get_leather_inventory_value()
            hardware_value = self._hardware_repository.get_hardware_inventory_value()
            supplies_value = self._supplies_repository.get_supplies_inventory_value()

            # Calculate total value
            total_value = (
                    leather_value.get("total_value", 0) +
                    hardware_value.get("total_value", 0) +
                    supplies_value.get("total_value", 0)
            )

            # Construct the report
            report = {
                "total_value": total_value,
                "leather_value": leather_value.get("total_value", 0),
                "hardware_value": hardware_value.get("total_value", 0),
                "supplies_value": supplies_value.get("total_value", 0),
                "by_category": {
                    "leather": leather_value,
                    "hardware": hardware_value,
                    "supplies": supplies_value
                },
                "date_generated": datetime.now().isoformat()
            }

            logger.info(f"Generated inventory value report: total value = {total_value:.2f}")
            return report

        except RepositoryError as e:
            logger.error(f"Error generating inventory value report: {str(e)}")
            raise ServiceError(f"Failed to generate inventory value report: {str(e)}")

    def get_materials_by_supplier(self, supplier_id: int) -> Dict[str, List[Material]]:
        """
        Get all materials from a specific supplier, grouped by category.

        Args:
            supplier_id: ID of the supplier

        Returns:
            Dictionary of materials by category
            (leather, hardware, supplies)
        """
        try:
            # Get materials from each repository
            leathers = self._leather_repository.get_materials_by_supplier(supplier_id)
            hardware = self._hardware_repository.get_hardware_by_supplier(supplier_id)
            supplies = self._supplies_repository.get_supplies_by_supplier(supplier_id)

            # Group results
            result = {
                "leather": leathers,
                "hardware": hardware,
                "supplies": supplies
            }

            logger.debug(
                f"Found materials from supplier {supplier_id}: {len(leathers)} leathers, "
                f"{len(hardware)} hardware items, {len(supplies)} supplies"
            )
            return result

        except RepositoryError as e:
            logger.error(f"Error getting materials by supplier {supplier_id}: {str(e)}")
            raise ServiceError(f"Failed to get materials by supplier: {str(e)}")

    # Additional utility methods

    def get_thread_inventory(self) -> List[Material]:
        """
        Get all thread materials with inventory information.

        Returns:
            List of thread materials
        """
        try:
            return self._supplies_repository.get_threads()
        except RepositoryError as e:
            logger.error(f"Error getting thread inventory: {str(e)}")
            raise ServiceError(f"Failed to get thread inventory: {str(e)}")

    def get_adhesive_inventory(self) -> List[Material]:
        """
        Get all adhesive materials with inventory information.

        Returns:
            List of adhesive materials
        """
        try:
            return self._supplies_repository.get_adhesives()
        except RepositoryError as e:
            logger.error(f"Error getting adhesive inventory: {str(e)}")
            raise ServiceError(f"Failed to get adhesive inventory: {str(e)}")

    def get_dye_inventory(self) -> List[Material]:
        """
        Get all dye materials with inventory information.

        Returns:
            List of dye materials
        """
        try:
            return self._supplies_repository.get_dyes()
        except RepositoryError as e:
            logger.error(f"Error getting dye inventory: {str(e)}")
            raise ServiceError(f"Failed to get dye inventory: {str(e)}")

    def get_edge_paint_inventory(self) -> List[Material]:
        """
        Get all edge paint materials with inventory information.

        Returns:
            List of edge paint materials
        """
        try:
            return self._supplies_repository.get_edge_paints()
        except RepositoryError as e:
            logger.error(f"Error getting edge paint inventory: {str(e)}")
            raise ServiceError(f"Failed to get edge paint inventory: {str(e)}")