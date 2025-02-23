# Path: services/material_management_service.py
"""
Comprehensive Material Management Service for Leatherworking Project

Provides advanced material tracking, allocation, and optimization features.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum, auto
import logging
from datetime import datetime, timedelta


class MaterialStatus(Enum):
    """Enum for material status tracking."""
    AVAILABLE = auto()
    RESERVED = auto()
    IN_USE = auto()
    DEPLETED = auto()
    DAMAGED = auto()


class MaterialAllocation:
    """
    Tracks material allocation across different projects and workflows.
    """

    def __init__(self, material_id: str, total_quantity: float):
        """
        Initialize material allocation tracking.

        Args:
            material_id (str): Unique identifier for the material
            total_quantity (float): Total available quantity of material
        """
        self.material_id = material_id
        self.total_quantity = total_quantity
        self.allocated_quantity = 0.0
        self.allocations: List[Dict[str, Any]] = []
        self.status = MaterialStatus.AVAILABLE

    def allocate(self, project_id: str, quantity: float, allocation_type: str = 'standard') -> bool:
        """
        Allocate material to a specific project.

        Args:
            project_id (str): Project identifier
            quantity (float): Quantity to allocate
            allocation_type (str): Type of allocation

        Returns:
            bool: Whether allocation was successful
        """
        if quantity > (self.total_quantity - self.allocated_quantity):
            return False

        allocation = {
            'project_id': project_id,
            'quantity': quantity,
            'type': allocation_type,
            'timestamp': datetime.now(),
            'status': 'active'
        }

        self.allocations.append(allocation)
        self.allocated_quantity += quantity

        # Update status
        if self.allocated_quantity >= self.total_quantity:
            self.status = MaterialStatus.DEPLETED

        return True

    def deallocate(self, project_id: str, quantity: float) -> bool:
        """
        Deallocate material from a project.

        Args:
            project_id (str): Project identifier
            quantity (float): Quantity to deallocate

        Returns:
            bool: Whether deallocation was successful
        """
        # Find and update allocation
        for allocation in self.allocations:
            if allocation['project_id'] == project_id and allocation['status'] == 'active':
                if allocation['quantity'] >= quantity:
                    allocation['quantity'] -= quantity
                    self.allocated_quantity -= quantity

                    # Update status if no longer depleted
                    if self.status == MaterialStatus.DEPLETED:
                        self.status = MaterialStatus.AVAILABLE

                    return True

        return False


@dataclass
class MaterialEfficiencyMetrics:
    """
    Tracks material efficiency and performance metrics.
    """
    material_id: str
    total_used: float = 0.0
    total_wasted: float = 0.0
    efficiency_rate: float = 0.0
    projects: List[str] = field(default_factory=list)

    def update_metrics(self, used: float, wasted: float, project_id: str):
        """
        Update material efficiency metrics.

        Args:
            used (float): Quantity of material used
            wasted (float): Quantity of material wasted
            project_id (str): Project identifier
        """
        self.total_used += used
        self.total_wasted += wasted
        self.projects.append(project_id)

        # Calculate efficiency rate
        if self.total_used > 0:
            self.efficiency_rate = (self.total_used / (self.total_used + self.total_wasted)) * 100


class MaterialManagementService:
    """
    Comprehensive service for managing material lifecycle and optimization.
    """

    def __init__(self):
        """Initialize material management service."""
        self.materials: Dict[str, MaterialAllocation] = {}
        self.efficiency_metrics: Dict[str, MaterialEfficiencyMetrics] = {}
        self.logger = logging.getLogger(__name__)

    def register_material(self, material_id: str, total_quantity: float, material_type: str = 'general'):
        """
        Register a new material in the system.

        Args:
            material_id (str): Unique material identifier
            total_quantity (float): Total available quantity
            material_type (str): Type of material
        """
        if material_id in self.materials:
            raise ValueError(f"Material {material_id} already exists")

        allocation = MaterialAllocation(material_id, total_quantity)
        efficiency = MaterialEfficiencyMetrics(material_id)

        self.materials[material_id] = allocation
        self.efficiency_metrics[material_id] = efficiency

        self.logger.info(f"Registered material: {material_id}")

    def allocate_material(self, material_id: str, project_id: str, quantity: float) -> bool:
        """
        Allocate material to a project.

        Args:
            material_id (str): Material to allocate
            project_id (str): Project receiving the material
            quantity (float): Quantity to allocate

        Returns:
            bool: Whether allocation was successful
        """
        if material_id not in self.materials:
            self.logger.error(f"Material {material_id} not found")
            return False

        allocation_success = self.materials[material_id].allocate(project_id, quantity)
        if allocation_success:
            self.logger.info(f"Allocated {quantity} of {material_id} to project {project_id}")

        return allocation_success

    def deallocate_material(self, material_id: str, project_id: str, quantity: float) -> bool:
        """
        Deallocate material from a project.

        Args:
            material_id (str): Material to deallocate
            project_id (str): Project returning the material
            quantity (float): Quantity to deallocate

        Returns:
            bool: Whether deallocation was successful
        """
        if material_id not in self.materials:
            self.logger.error(f"Material {material_id} not found")
            return False

        deallocation_success = self.materials[material_id].deallocate(project_id, quantity)
        if deallocation_success:
            self.logger.info(f"Deallocated {quantity} of {material_id} from project {project_id}")

        return deallocation_success

    def update_material_efficiency(self, material_id: str, project_id: str, used: float, wasted: float):
        """
        Update material efficiency metrics.

        Args:
            material_id (str): Material identifier
            project_id (str): Project identifier
            used (float): Quantity of material used
            wasted (float): Quantity of material wasted
        """
        if material_id not in self.efficiency_metrics:
            self.logger.error(f"Material {material_id} not found in efficiency tracking")
            return

        self.efficiency_metrics[material_id].update_metrics(used, wasted, project_id)
        self.logger.info(f"Updated efficiency for material {material_id} in project {project_id}")

    def get_material_efficiency_report(self, material_id: Optional[str] = None) -> Dict:
        """
        Generate material efficiency report.

        Args:
            material_id (Optional[str]): Specific material to report on

        Returns:
            Dict: Efficiency report for material(s)
        """
        if material_id:
            if material_id not in self.efficiency_metrics:
                return {}

            metrics = self.efficiency_metrics[material_id]
            return {
                'material_id': metrics.material_id,
                'total_used': metrics.total_used,
                'total_wasted': metrics.total_wasted,
                'efficiency_rate': metrics.efficiency_rate,
                'projects': metrics.projects
            }

        # Generate report for all materials
        return {
            mid: self.get_material_efficiency_report(mid)
            for mid in self.efficiency_metrics.keys()
        }

    def get_material_allocation_status(self, material_id: Optional[str] = None) -> Dict:
        """
        Get current allocation status of materials.

        Args:
            material_id (Optional[str]): Specific material to check

        Returns:
            Dict: Allocation status for material(s)
        """
        if material_id:
            if material_id not in self.materials:
                return {}

            allocation = self.materials[material_id]
            return {
                'material_id': allocation.material_id,
                'total_quantity': allocation.total_quantity,
                'allocated_quantity': allocation.allocated_quantity,
                'status': allocation.status.name,
                'allocations': allocation.allocations
            }

        # Return status for all materials
        return {
            mid: self.get_material_allocation_status(mid)
            for mid in self.materials.keys()
        }


def main():
    """
    Demonstration of Material Management Service functionality.
    """
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Create service
    material_service = MaterialManagementService()

    # Register some materials
    material_service.register_material('LEATHER-001', 100.0, 'full_grain')
    material_service.register_material('THREAD-001', 500.0, 'polyester')

    # Allocate materials to projects
    material_service.allocate_material('LEATHER-001', 'PROJECT-BAG-001', 25.5)
    material_service.allocate_material('THREAD-001', 'PROJECT-BAG-001', 100.0)

    # Update material efficiency
    material_service.update_material_efficiency('LEATHER-001', 'PROJECT-BAG-001', used=20.0, wasted=5.5)

    # Get reports
    print("Material Efficiency Report:")
    print(material_service.get_material_efficiency_report())

    print("\nMaterial Allocation Status:")
    print(material_service.get_material_allocation_status())


if __name__ == "__main__":
    main()
