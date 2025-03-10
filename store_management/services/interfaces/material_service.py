from typing import Protocol, Dict, List, Optional, Union
from datetime import datetime

from database.models.enums import (
    MaterialType,
    LeatherType,
    HardwareType,
    InventoryStatus,
    QualityGrade,
    SupplierStatus,
    TransactionType
)


class IMaterialService(Protocol):
    """
    Comprehensive interface for Material Service operations.
    Defines the contract for material-related business logic across different material types.
    """

    def create_material(
            self,
            material_type: MaterialType,
            **kwargs
    ) -> Dict:
        """
        Create a new material entry with comprehensive details.

        Args:
            material_type: Type of material
            **kwargs: Detailed material-specific information

        Returns:
            Dict: Created material information
        """
        ...

    def update_material(
            self,
            material_id: int,
            **kwargs
    ) -> Dict:
        """
        Update an existing material's information.

        Args:
            material_id: Unique identifier for the material
            **kwargs: Material details to update

        Returns:
            Dict: Updated material information
        """
        ...

    def get_material_by_id(
            self,
            material_id: int
    ) -> Optional[Dict]:
        """
        Retrieve comprehensive material details by ID.

        Args:
            material_id: Unique identifier for the material

        Returns:
            Detailed material information including inventory, components, etc.
        """
        ...

    def list_materials(
            self,
            material_type: Optional[MaterialType] = None,
            status: Optional[InventoryStatus] = None,
            quality: Optional[QualityGrade] = None,
            supplier_id: Optional[int] = None,
            min_quantity: Optional[float] = None,
            max_quantity: Optional[float] = None
    ) -> List[Dict]:
        """
        Advanced material listing with multiple filtering options.

        Args:
            material_type: Filter by material type
            status: Filter by inventory status
            quality: Filter by material quality
            supplier_id: Filter by supplier
            min_quantity: Minimum inventory quantity
            max_quantity: Maximum inventory quantity

        Returns:
            List of material details with advanced filtering
        """
        ...

    def delete_material(self, material_id: int) -> bool:
        """
        Soft or hard delete a material entry.

        Args:
            material_id: Unique identifier for the material

        Returns:
            Boolean indicating successful deletion
        """
        ...

    def validate_material_data(
            self,
            material_data: Dict,
            material_type: MaterialType
    ) -> bool:
        """
        Comprehensive validation of material data.

        Args:
            material_data: Material information to validate
            material_type: Type of material for specific validation

        Returns:
            Boolean indicating data validity
        """
        ...

    def calculate_material_cost(
            self,
            material_id: int,
            quantity: float
    ) -> float:
        """
        Calculate the total cost for a specific quantity of material.

        Args:
            material_id: Unique identifier for the material
            quantity: Amount of material

        Returns:
            Total cost for the material quantity
        """
        ...

    def get_material_inventory(
            self,
            material_id: int
    ) -> Dict:
        """
        Retrieve detailed inventory information for a material.

        Args:
            material_id: Unique identifier for the material

        Returns:
            Detailed inventory information
        """
        ...

    def track_material_usage(
            self,
            material_id: int,
            quantity: float,
            transaction_type: TransactionType
    ) -> Dict:
        """
        Track material usage across different transaction types.

        Args:
            material_id: Unique identifier for the material
            quantity: Quantity of material used/added
            transaction_type: Type of transaction (purchase, usage, etc.)

        Returns:
            Updated material transaction record
        """
        ...

    def get_material_components(
            self,
            material_id: int
    ) -> List[Dict]:
        """
        Retrieve components that use this material.

        Args:
            material_id: Unique identifier for the material

        Returns:
            List of components using this material
        """
        ...

    def get_material_purchase_history(
            self,
            material_id: int,
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None
    ) -> List[Dict]:
        """
        Retrieve purchase history for a specific material.

        Args:
            material_id: Unique identifier for the material
            start_date: Optional start date for purchase history
            end_date: Optional end date for purchase history

        Returns:
            List of purchase records for the material
        """
        ...

    def check_material_low_stock(
            self,
            material_id: int,
            threshold: Optional[float] = None
    ) -> bool:
        """
        Check if material is below stock threshold.

        Args:
            material_id: Unique identifier for the material
            threshold: Optional custom low stock threshold

        Returns:
            Boolean indicating if material is low in stock
        """
        ...

    def get_material_supplier(
            self,
            material_id: int
    ) -> Optional[Dict]:
        """
        Retrieve supplier information for a material.

        Args:
            material_id: Unique identifier for the material

        Returns:
            Supplier details for the material
        """
        ...