#!/usr/bin/env python3
# Path: services/interfaces.py
"""
Service interfaces module defining the contract for all service implementations.

This module contains interface definitions for various service types used throughout
the application, providing a clear contract that concrete implementations must fulfill.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, TypeVar, Generic

# Generic type for entities
T = TypeVar('T')


class BaseService(ABC, Generic[T]):
    """
    Generic base service interface with common CRUD operations.
    """

    @abstractmethod
    def create(self, data: Dict) -> T:
        """
        Create a new entity.

        Args:
            data (Dict): The data to create the entity with

        Returns:
            T: The created entity
        """
        pass

    @abstractmethod
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Retrieve an entity by its ID.

        Args:
            id (int): The unique identifier of the entity

        Returns:
            Optional[T]: The entity if found, None otherwise
        """
        pass

    @abstractmethod
    def update(self, id: int, data: Dict) -> Optional[T]:
        """
        Update an existing entity.

        Args:
            id (int): The unique identifier of the entity to update
            data (Dict): The updated data

        Returns:
            Optional[T]: The updated entity if successful, None otherwise
        """
        pass

    @abstractmethod
    def delete(self, id: int) -> bool:
        """
        Delete an entity by its ID.

        Args:
            id (int): The unique identifier of the entity to delete

        Returns:
            bool: True if deletion was successful, False otherwise
        """
        pass

    @abstractmethod
    def search(self, query: str, filters: Dict = None) -> List[T]:
        """
        Search for entities based on query and filters.

        Args:
            query (str): The search query
            filters (Dict, optional): Additional filters to apply

        Returns:
            List[T]: A list of matching entities
        """
        pass


class MaterialService(BaseService):
    """
    Interface for material-related operations.
    """

    @abstractmethod
    def update_stock(self, material_id: int, quantity: float, transaction_type: str) -> None:
        """
        Update material stock.

        Args:
            material_id (int): The unique identifier of the material
            quantity (float): The quantity to update
            transaction_type (str): The type of transaction (e.g., "add", "remove")
        """
        pass

    @abstractmethod
    def get_low_stock_materials(self) -> List:
        """
        Retrieve materials with low stock.

        Returns:
            List: A list of materials with low stock levels
        """
        pass


class ProjectService(BaseService):
    """
    Interface for project-related operations.
    """

    @abstractmethod
    def create_project(self, project_data: Dict) -> 'Project':
        """
        Create a new project.

        Args:
            project_data (Dict): The project data

        Returns:
            Project: The created project
        """
        pass

    @abstractmethod
    def update_project_status(self, project_id: int, status: str) -> None:
        """
        Update project status.

        Args:
            project_id (int): The unique identifier of the project
            status (str): The new status
        """
        pass

    @abstractmethod
    def analyze_project_material_usage(self, project_id: int) -> Dict:
        """
        Analyze material usage for a project.

        Args:
            project_id (int): The unique identifier of the project

        Returns:
            Dict: Analysis results of material usage
        """
        pass


class InventoryService(BaseService):
    """
    Interface for inventory management operations.
    """

    @abstractmethod
    def adjust_stock(self, item_id: int, quantity_change: float, transaction_type: str) -> None:
        """
        Adjust stock for an inventory item.

        Args:
            item_id (int): The unique identifier of the inventory item
            quantity_change (float): The amount to change
            transaction_type (str): The type of transaction
        """
        pass

    @abstractmethod
    def get_inventory_summary(self) -> List[Dict]:
        """
        Get summary of current inventory.

        Returns:
            List[Dict]: A list of inventory summary items
        """
        pass


class OrderService(BaseService):
    """
    Interface for order-related operations.
    """

    @abstractmethod
    def process_order(self, order_data: Dict) -> 'Order':
        """
        Process a new order.

        Args:
            order_data (Dict): The order data

        Returns:
            Order: The processed order
        """
        pass

    @abstractmethod
    def get_orders_by_status(self, status: str) -> List['Order']:
        """
        Retrieve orders by status.

        Args:
            status (str): The status to filter by

        Returns:
            List[Order]: A list of matching orders
        """
        pass


class SupplierService(BaseService):
    """
    Interface for supplier-related operations.
    """

    @abstractmethod
    def evaluate_supplier_performance(self, supplier_id: int, period: datetime) -> Dict:
        """
        Evaluate supplier performance.

        Args:
            supplier_id (int): The unique identifier of the supplier
            period (datetime): The time period to evaluate

        Returns:
            Dict: Performance evaluation results
        """
        pass