# services/implementations/inventory_service.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Tuple

from utils.circular_import_resolver import CircularImportResolver
from services.interfaces.inventory_service import IInventoryService
from services.interfaces.material_service import MaterialType


class InventoryService(IInventoryService):
    """Implementation of the Inventory Service for managing leatherworking inventory."""

    def __init__(self):
        """Initialize the inventory service."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("InventoryService initialized")

        # In-memory storage for demonstration purposes
        self._inventory_items = {}
        self._inventory_transactions = []
        self._reserved_materials = {}

        # Specific collections for leathers and parts
        self._leathers = {}
        self._parts = {}

    def add_inventory_item(self, item_type: MaterialType, name: str,
                           quantity: float, unit_price: float,
                           description: Optional[str] = None,
                           supplier_id: Optional[str] = None,
                           location_id: Optional[str] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a new item to inventory.

        Args:
            item_type: Type of material
            name: Item name
            quantity: Initial quantity
            unit_price: Price per unit
            description: Optional description
            supplier_id: Optional supplier ID
            location_id: Optional storage location ID
            metadata: Additional item metadata

        Returns:
            Dict[str, Any]: Created inventory item
        """
        item_id = f"INV{len(self._inventory_items) + 1:04d}"
        now = datetime.now()

        inventory_item = {
            "id": item_id,
            "item_type": item_type,
            "name": name,
            "quantity": quantity,
            "unit_price": unit_price,
            "description": description,
            "supplier_id": supplier_id,
            "location_id": location_id,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
            "status": "IN_STOCK"
        }

        self._inventory_items[item_id] = inventory_item

        # Add to specific collections based on type
        if item_type == MaterialType.LEATHER:
            leather_id = f"L{len(self._leathers) + 1:04d}"
            leather = inventory_item.copy()
            leather["leather_id"] = leather_id
            leather["area"] = metadata.get("area", 0.0) if metadata else 0.0
            leather["thickness"] = metadata.get("thickness", 0.0) if metadata else 0.0
            leather["quality_grade"] = metadata.get("quality_grade", "STANDARD") if metadata else "STANDARD"
            self._leathers[leather_id] = leather

        elif item_type in [MaterialType.HARDWARE, MaterialType.THREAD, MaterialType.ADHESIVE]:
            part_id = f"P{len(self._parts) + 1:04d}"
            part = inventory_item.copy()
            part["part_id"] = part_id
            part["part_number"] = metadata.get("part_number", "") if metadata else ""
            part["reorder_level"] = metadata.get("reorder_level", 5) if metadata else 5
            self._parts[part_id] = part

        # Record the initial transaction
        self._record_transaction(
            item_id=item_id,
            transaction_type="INITIAL",
            quantity=quantity,
            unit_price=unit_price
        )

        self.logger.info(f"Added inventory item: {name} (ID: {item_id})")
        return inventory_item

    def get_inventory_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Get an inventory item by ID.

        Args:
            item_id: ID of the inventory item to retrieve

        Returns:
            Optional[Dict[str, Any]]: Inventory item data or None if not found
        """
        item = self._inventory_items.get(item_id)
        if not item:
            self.logger.warning(f"Inventory item not found: {item_id}")
            return None

        return item

    def update_inventory_item(self, item_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an inventory item.

        Args:
            item_id: ID of the inventory item to update
            updates: Dictionary of fields to update

        Returns:
            Optional[Dict[str, Any]]: Updated inventory item or None if not found
        """
        if item_id not in self._inventory_items:
            self.logger.warning(f"Cannot update non-existent inventory item: {item_id}")
            return None

        item = self._inventory_items[item_id]

        # Update only valid fields
        valid_fields = [
            "name", "description", "unit_price", "supplier_id",
            "location_id", "metadata", "status"
        ]

        for field, value in updates.items():
            if field in valid_fields:
                item[field] = value

        # Special handling for quantity
        if "quantity" in updates:
            old_quantity = item["quantity"]
            new_quantity = updates["quantity"]
            quantity_change = new_quantity - old_quantity

            if quantity_change != 0:
                transaction_type = "INCREASE" if quantity_change > 0 else "DECREASE"
                self._record_transaction(
                    item_id=item_id,
                    transaction_type=transaction_type,
                    quantity=abs(quantity_change),
                    unit_price=item["unit_price"]
                )

                item["quantity"] = new_quantity

        # Always update the 'updated_at' timestamp
        item["updated_at"] = datetime.now()

        # Update status based on quantity
        if item["quantity"] <= 0:
            item["status"] = "OUT_OF_STOCK"
        elif item["quantity"] < 10:  # Arbitrary low threshold
            item["status"] = "LOW_STOCK"
        else:
            item["status"] = "IN_STOCK"

        # Update in specific collections if needed
        item_type = item.get("item_type")
        if item_type == MaterialType.LEATHER:
            # Find the corresponding leather entry
            for leather_id, leather in self._leathers.items():
                if leather.get("id") == item_id:
                    # Update leather with applicable fields
                    for field in valid_fields:
                        if field in updates:
                            leather[field] = updates[field]

                    if "quantity" in updates:
                        leather["quantity"] = new_quantity

                    if "metadata" in updates and updates["metadata"]:
                        if "area" in updates["metadata"]:
                            leather["area"] = updates["metadata"]["area"]
                        if "thickness" in updates["metadata"]:
                            leather["thickness"] = updates["metadata"]["thickness"]
                        if "quality_grade" in updates["metadata"]:
                            leather["quality_grade"] = updates["metadata"]["quality_grade"]

                    leather["updated_at"] = item["updated_at"]
                    leather["status"] = item["status"]
                    break

        elif item_type in [MaterialType.HARDWARE, MaterialType.THREAD, MaterialType.ADHESIVE]:
            # Find the corresponding part entry
            for part_id, part in self._parts.items():
                if part.get("id") == item_id:
                    # Update part with applicable fields
                    for field in valid_fields:
                        if field in updates:
                            part[field] = updates[field]

                    if "quantity" in updates:
                        part["quantity"] = new_quantity

                    if "metadata" in updates and updates["metadata"]:
                        if "part_number" in updates["metadata"]:
                            part["part_number"] = updates["metadata"]["part_number"]
                        if "reorder_level" in updates["metadata"]:
                            part["reorder_level"] = updates["metadata"]["reorder_level"]

                    part["updated_at"] = item["updated_at"]
                    part["status"] = item["status"]
                    break

        self.logger.info(f"Updated inventory item: {item_id}")
        return item

    def update_leather_area(self, leather_id: str, new_area: float) -> Optional[Dict[str, Any]]:
        """Update the area of a leather item.

        Args:
            leather_id: ID of the leather
            new_area: New area value

        Returns:
            Optional[Dict[str, Any]]: Updated leather item or None if not found
        """
        if leather_id not in self._leathers:
            self.logger.warning(f"Cannot update non-existent leather: {leather_id}")
            return None

        leather = self._leathers[leather_id]
        old_area = leather.get("area", 0.0)
        leather["area"] = new_area
        leather["updated_at"] = datetime.now()

        # Update the main inventory item if it exists
        inventory_id = leather.get("id")
        if inventory_id and inventory_id in self._inventory_items:
            if "metadata" not in self._inventory_items[inventory_id]:
                self._inventory_items[inventory_id]["metadata"] = {}

            self._inventory_items[inventory_id]["metadata"]["area"] = new_area
            self._inventory_items[inventory_id]["updated_at"] = leather["updated_at"]

        self.logger.info(f"Updated leather {leather_id} area from {old_area} to {new_area}")
        return leather

    def update_part_stock(self, part_id: str, new_quantity: float,
                          transaction_note: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Update the stock quantity of a part.

        Args:
            part_id: ID of the part
            new_quantity: New quantity value
            transaction_note: Optional note about the transaction

        Returns:
            Optional[Dict[str, Any]]: Updated part or None if not found
        """
        if part_id not in self._parts:
            self.logger.warning(f"Cannot update non-existent part: {part_id}")
            return None

        part = self._parts[part_id]
        old_quantity = part.get("quantity", 0.0)
        quantity_change = new_quantity - old_quantity

        part["quantity"] = new_quantity
        part["updated_at"] = datetime.now()

        # Update status based on quantity
        reorder_level = part.get("reorder_level", 5)
        if new_quantity <= 0:
            part["status"] = "OUT_OF_STOCK"
        elif new_quantity < reorder_level:
            part["status"] = "LOW_STOCK"
        else:
            part["status"] = "IN_STOCK"

        # Update the main inventory item if it exists
        inventory_id = part.get("id")
        if inventory_id and inventory_id in self._inventory_items:
            self._inventory_items[inventory_id]["quantity"] = new_quantity
            self._inventory_items[inventory_id]["updated_at"] = part["updated_at"]
            self._inventory_items[inventory_id]["status"] = part["status"]

            # Record transaction
            transaction_type = "INCREASE" if quantity_change > 0 else "DECREASE"
            self._record_transaction(
                item_id=inventory_id,
                transaction_type=transaction_type,
                quantity=abs(quantity_change),
                unit_price=self._inventory_items[inventory_id].get("unit_price", 0.0),
                notes=transaction_note
            )

        self.logger.info(f"Updated part {part_id} quantity from {old_quantity} to {new_quantity}")
        return part

    def delete_inventory_item(self, item_id: str) -> bool:
        """Delete an inventory item.

        Args:
            item_id: ID of the inventory item to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if item_id not in self._inventory_items:
            self.logger.warning(f"Cannot delete non-existent inventory item: {item_id}")
            return False

        item = self._inventory_items[item_id]
        item_type = item.get("item_type")

        # Remove from specific collections if needed
        if item_type == MaterialType.LEATHER:
            # Find and remove from leathers
            leather_to_remove = None
            for leather_id, leather in self._leathers.items():
                if leather.get("id") == item_id:
                    leather_to_remove = leather_id
                    break

            if leather_to_remove:
                del self._leathers[leather_to_remove]

        elif item_type in [MaterialType.HARDWARE, MaterialType.THREAD, MaterialType.ADHESIVE]:
            # Find and remove from parts
            part_to_remove = None
            for part_id, part in self._parts.items():
                if part.get("id") == item_id:
                    part_to_remove = part_id
                    break

            if part_to_remove:
                del self._parts[part_to_remove]

        # Remove from main inventory
        del self._inventory_items[item_id]

        self.logger.info(f"Deleted inventory item: {item_id}")
        return True

    def list_inventory_items(self, item_type: Optional[MaterialType] = None,
                             location_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all inventory items, optionally filtered by type or location.

        Args:
            item_type: Optional filter by item type
            location_id: Optional filter by storage location

        Returns:
            List[Dict[str, Any]]: List of inventory items
        """
        result = []

        for item in self._inventory_items.values():
            if item_type and item["item_type"] != item_type:
                continue

            if location_id and item["location_id"] != location_id:
                continue

            result.append(item)

        return result

    def search_inventory(self, query: str) -> List[Dict[str, Any]]:
        """Search for inventory items by name or description.

        Args:
            query: Search query string

        Returns:
            List[Dict[str, Any]]: List of matching inventory items
        """
        query = query.lower()
        results = []

        for item in self._inventory_items.values():
            if (query in item["name"].lower() or
                    (item["description"] and query in item["description"].lower())):
                results.append(item)

        return results

    def get_low_stock_items(self, threshold: float = 10.0) -> List[Dict[str, Any]]:
        """Get inventory items with quantity below the threshold.

        Args:
            threshold: Quantity threshold

        Returns:
            List[Dict[str, Any]]: List of low stock items
        """
        return [item for item in self._inventory_items.values() if item["quantity"] < threshold]

    def get_low_stock_leather(self, area_threshold: float = 5.0) -> List[Dict[str, Any]]:
        """Get leather items with area below the threshold.

        Args:
            area_threshold: Area threshold in square feet/meters

        Returns:
            List[Dict[str, Any]]: List of low stock leather items
        """
        return [leather for leather in self._leathers.values()
                if leather.get("area", 0.0) < area_threshold]

    def get_low_stock_parts(self) -> List[Dict[str, Any]]:
        """Get parts where quantity is below reorder level.

        Returns:
            List[Dict[str, Any]]: List of parts below reorder level
        """
        low_stock_parts = []
        for part in self._parts.values():
            reorder_level = part.get("reorder_level", 5)
            if part.get("quantity", 0) < reorder_level:
                low_stock_parts.append(part)

        return low_stock_parts

    def adjust_inventory_quantity(self, item_id: str, quantity_change: float,
                                  notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Adjust the quantity of an inventory item.

        Args:
            item_id: ID of the inventory item
            quantity_change: Amount to change (positive or negative)
            notes: Optional notes about the adjustment

        Returns:
            Optional[Dict[str, Any]]: Updated inventory item or None if not found
        """
        if item_id not in self._inventory_items:
            self.logger.warning(f"Cannot adjust quantity for non-existent item: {item_id}")
            return None

        item = self._inventory_items[item_id]
        old_quantity = item["quantity"]
        new_quantity = max(0, old_quantity + quantity_change)  # Prevent negative inventory

        transaction_type = "INCREASE" if quantity_change > 0 else "DECREASE"
        self._record_transaction(
            item_id=item_id,
            transaction_type=transaction_type,
            quantity=abs(quantity_change),
            unit_price=item["unit_price"],
            notes=notes
        )

        item["quantity"] = new_quantity
        item["updated_at"] = datetime.now()

        # Update status based on quantity
        if new_quantity <= 0:
            item["status"] = "OUT_OF_STOCK"
        elif new_quantity < 10:  # Arbitrary low threshold
            item["status"] = "LOW_STOCK"
        else:
            item["status"] = "IN_STOCK"

        # Update in specific collections if needed
        item_type = item.get("item_type")
        if item_type == MaterialType.LEATHER:
            # Find and update leather
            for leather_id, leather in self._leathers.items():
                if leather.get("id") == item_id:
                    leather["quantity"] = new_quantity
                    leather["updated_at"] = item["updated_at"]
                    leather["status"] = item["status"]
                    break

        elif item_type in [MaterialType.HARDWARE, MaterialType.THREAD, MaterialType.ADHESIVE]:
            # Find and update part
            for part_id, part in self._parts.items():
                if part.get("id") == item_id:
                    part["quantity"] = new_quantity
                    part["updated_at"] = item["updated_at"]
                    part["status"] = item["status"]
                    break

        self.logger.info(f"Adjusted inventory item {item_id} quantity from {old_quantity} to {new_quantity}")
        return item

    def transfer_inventory(self, item_id: str, to_location_id: str,
                           quantity: Optional[float] = None,
                           notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Transfer inventory to a different location.

        Args:
            item_id: ID of the inventory item
            to_location_id: ID of the destination location
            quantity: Quantity to transfer (if None, transfers all)
            notes: Optional notes about the transfer

        Returns:
            Optional[Dict[str, Any]]: Updated inventory item or None if not found
        """
        if item_id not in self._inventory_items:
            self.logger.warning(f"Cannot transfer non-existent item: {item_id}")
            return None

        item = self._inventory_items[item_id]

        if quantity is None or quantity >= item["quantity"]:
            # Transfer all quantity
            transfer_quantity = item["quantity"]

            # Update location
            from_location = item["location_id"]
            item["location_id"] = to_location_id

            self.logger.info(f"Transferred all inventory of item {item_id} from {from_location} to {to_location_id}")
        else:
            # Split the inventory
            transfer_quantity = quantity
            remaining_quantity = item["quantity"] - quantity

            # Create a new inventory item at the destination
            new_item = self.add_inventory_item(
                item_type=item["item_type"],
                name=item["name"],
                quantity=transfer_quantity,
                unit_price=item["unit_price"],
                description=item["description"],
                supplier_id=item["supplier_id"],
                location_id=to_location_id,
                metadata=item["metadata"].copy()
            )

            # Reduce the quantity of the original item
            item["quantity"] = remaining_quantity
            item["updated_at"] = datetime.now()

            self.logger.info(
                f"Transferred {transfer_quantity} of item {item_id} to new item {new_item['id']} at location {to_location_id}"
            )

        # Record the transaction
        self._record_transaction(
            item_id=item_id,
            transaction_type="TRANSFER",
            quantity=transfer_quantity,
            unit_price=item["unit_price"],
            notes=f"Transferred to location {to_location_id}. {notes}" if notes else f"Transferred to location {to_location_id}"
        )

        return item

    def reserve_materials(self, materials: List[Dict[str, Any]],
                          project_id: str) -> Tuple[bool, List[Dict[str, Any]]]:
        """Reserve materials for a project.

        Args:
            materials: List of materials to reserve (each with item_id and quantity)
            project_id: ID of the project reserving the materials

        Returns:
            Tuple[bool, List[Dict[str, Any]]]: Success flag and list of unavailable materials
        """
        unavailable = []
        reserved_items = []

        # First check availability
        for material in materials:
            item_id = material.get("item_id")
            quantity = material.get("quantity", 0)

            if not item_id or not quantity:
                continue

            if item_id not in self._inventory_items:
                unavailable.append({
                    "item_id": item_id,
                    "name": material.get("name", "Unknown"),
                    "requested": quantity,
                    "available": 0,
                    "reason": "ITEM_NOT_FOUND"
                })
                continue

            item = self._inventory_items[item_id]
            available = item["quantity"]

            # Check for existing reservations
            reserved = 0
            for res in self._reserved_materials.values():
                for res_item in res:
                    if res_item.get("item_id") == item_id:
                        reserved += res_item.get("quantity", 0)

            available_after_reservations = available - reserved

            if available_after_reservations < quantity:
                unavailable.append({
                    "item_id": item_id,
                    "name": item["name"],
                    "requested": quantity,
                    "available": available_after_reservations,
                    "reason": "INSUFFICIENT_QUANTITY"
                })
                continue

            # Item is available
            reserved_items.append({
                "item_id": item_id,
                "name": item["name"],
                "quantity": quantity,
                "unit_price": item["unit_price"],
                "reservation_time": datetime.now()
            })

        # If any items are unavailable, return failure
        if unavailable:
            return False, unavailable

        # All items are available, reserve them
        self._reserved_materials[project_id] = reserved_items

        # Log the reservation
        self.logger.info(f"Reserved {len(reserved_items)} materials for project {project_id}")

        return True, []

    def release_reserved_materials(self, project_id: str) -> bool:
        """Release materials that were reserved for a project.

        Args:
            project_id: ID of the project

        Returns:
            bool: True if successful, False otherwise
        """
        if project_id not in self._reserved_materials:
            self.logger.warning(f"No materials reserved for project {project_id}")
            return False

        # Remove the reservations
        del self._reserved_materials[project_id]

        self.logger.info(f"Released reserved materials for project {project_id}")
        return True

    def check_material_availability(self, materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check availability of materials.

        Args:
            materials: List of materials to check (each with item_id and quantity)

        Returns:
            List[Dict[str, Any]]: Availability status for each material
        """
        availability = []

        for material in materials:
            item_id = material.get("item_id")
            quantity = material.get("quantity", 0)

            if not item_id or not quantity:
                continue

            if item_id not in self._inventory_items:
                availability.append({
                    "item_id": item_id,
                    "name": material.get("name", "Unknown"),
                    "requested": quantity,
                    "available": 0,
                    "sufficient": False,
                    "status": "NOT_FOUND"
                })
                continue

            item = self._inventory_items[item_id]
            available = item["quantity"]

            # Check for existing reservations
            reserved = 0
            for res in self._reserved_materials.values():
                for res_item in res:
                    if res_item.get("item_id") == item_id:
                        reserved += res_item.get("quantity", 0)

            available_after_reservations = available - reserved

            availability.append({
                "item_id": item_id,
                "name": item["name"],
                "requested": quantity,
                "available": available,
                "available_unreserved": available_after_reservations,
                "reserved": reserved,
                "sufficient": available_after_reservations >= quantity,
                "status": item["status"]
            })

        return availability

    def get_inventory_value(self, item_type: Optional[MaterialType] = None) -> Dict[str, float]:
        """Calculate the total value of inventory.

        Args:
            item_type: Optional filter by item type

        Returns:
            Dict[str, float]: Dictionary with total value and item type breakdown
        """
        total_value = 0.0
        type_breakdown = {}

        for item in self._inventory_items.values():
            if item_type and item["item_type"] != item_type:
                continue

            item_value = item["quantity"] * item["unit_price"]
            total_value += item_value

            # Add to type breakdown
            item_type_str = str(item["item_type"])
            if item_type_str not in type_breakdown:
                type_breakdown[item_type_str] = 0.0
            type_breakdown[item_type_str] += item_value

        return {
            "total_value": total_value,
            "breakdown": type_breakdown
        }

    def generate_inventory_report(self, include_details: bool = False) -> Dict[str, Any]:
        """Generate a comprehensive inventory report.

        Args:
            include_details: Whether to include detailed item information

        Returns:
            Dict[str, Any]: Inventory report
        """
        # Count items and value by type
        type_counts = {}
        type_values = {}
        total_items = 0
        total_value = 0.0
        low_stock_count = 0
        out_of_stock_count = 0

        for item in self._inventory_items.values():
            item_type = str(item["item_type"])

            # Count
            if item_type not in type_counts:
                type_counts[item_type] = 0
            type_counts[item_type] += 1
            total_items += 1

            # Value
            item_value = item["quantity"] * item["unit_price"]
            if item_type not in type_values:
                type_values[item_type] = 0.0
            type_values[item_type] += item_value
            total_value += item_value

            # Stock status
            if item["status"] == "LOW_STOCK":
                low_stock_count += 1
            elif item["status"] == "OUT_OF_STOCK":
                out_of_stock_count += 1

        # Calculate leather stats
        total_leather_area = sum(leather.get("area", 0.0) for leather in self._leathers.values())
        leather_count = len(self._leathers)

        # Calculate parts stats
        parts_below_reorder = [
            part for part in self._parts.values()
            if part.get("quantity", 0) < part.get("reorder_level", 5)
        ]

        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_items": total_items,
                "total_value": total_value,
                "leather_count": leather_count,
                "total_leather_area": total_leather_area,
                "parts_count": len(self._parts),
                "parts_below_reorder": len(parts_below_reorder),
                "low_stock_count": low_stock_count,
                "out_of_stock_count": out_of_stock_count
            },
            "by_type": {
                "counts": type_counts,
                "values": type_values
            },
            "recommended_actions": []
        }

        # Add recommended actions
        if out_of_stock_count > 0:
            report["recommended_actions"].append({
                "type": "RESTOCK",
                "priority": "HIGH",
                "description": f"Restock {out_of_stock_count} out-of-stock items."
            })

        if low_stock_count > 0:
            report["recommended_actions"].append({
                "type": "ORDER",
                "priority": "MEDIUM",
                "description": f"Order {low_stock_count} low-stock items soon."
            })

        if len(parts_below_reorder) > 0:
            report["recommended_actions"].append({
                "type": "REORDER",
                "priority": "MEDIUM",
                "description": f"Reorder {len(parts_below_reorder)} parts that are below reorder level."
            })

        # Add details if requested
        if include_details:
            report["items"] = list(self._inventory_items.values())
            report["leathers"] = list(self._leathers.values())
            report["parts"] = list(self._parts.values())
            report["reserved_materials"] = self._reserved_materials

        self.logger.info(f"Generated inventory report with {total_items} items")
        return report

    def get_inventory_transactions(self, item_id: Optional[str] = None,
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """Get inventory transactions history.

        Args:
            item_id: Optional filter by item ID
            limit: Maximum number of transactions to return

        Returns:
            List[Dict[str, Any]]: List of inventory transactions
        """
        transactions = self._inventory_transactions

        if item_id:
            transactions = [t for t in transactions if t["item_id"] == item_id]

        # Return most recent transactions first
        return sorted(transactions, key=lambda t: t["timestamp"], reverse=True)[:limit]

    def _record_transaction(self, item_id: str, transaction_type: str, quantity: float,
                            unit_price: float, notes: Optional[str] = None) -> Dict[str, Any]:
        """Record an inventory transaction.

        Args:
            item_id: ID of the inventory item
            transaction_type: Type of transaction
            quantity: Quantity involved
            unit_price: Unit price at time of transaction
            notes: Optional notes about the transaction

        Returns:
            Dict[str, Any]: Recorded transaction
        """
        transaction = {
            "id": f"TX{len(self._inventory_transactions) + 1:06d}",
            "item_id": item_id,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_value": quantity * unit_price,
            "timestamp": datetime.now(),
            "notes": notes
        }

        self._inventory_transactions.append(transaction)
        return transaction