# services/implementations/pattern_service.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from utils.circular_import_resolver import CircularImportResolver
from services.interfaces.pattern_service import IPatternService, PatternStatus

# Use lazy imports to avoid circular imports
Pattern = CircularImportResolver.lazy_import("database.models.pattern", "Pattern")


class PatternService(IPatternService):
    """Implementation of the Pattern Service for managing leatherworking patterns."""

    def __init__(self):
        """Initialize the pattern service."""
        self.logger = logging.getLogger(__name__)
        self.logger.info("PatternService initialized")

        # In-memory storage for demonstration/fallback purposes
        self._patterns = {}

    def create_pattern(self, name: str, description: Optional[str] = None,
                       instructions: Optional[str] = None,
                       complexity_level: int = 1,
                       metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new pattern.

        Args:
            name: Pattern name
            description: Optional pattern description
            instructions: Optional pattern instructions
            complexity_level: Complexity level (1-5)
            metadata: Additional pattern metadata

        Returns:
            Dict[str, Any]: Created pattern data
        """
        pattern_id = f"PT{len(self._patterns) + 1:04d}"
        now = datetime.now()

        pattern = {
            "id": pattern_id,
            "name": name,
            "description": description,
            "instructions": instructions,
            "complexity_level": max(1, min(5, complexity_level)),  # Clamp between 1-5
            "status": PatternStatus.DRAFT,
            "created_at": now,
            "updated_at": now,
            "metadata": metadata or {},
            "components": []
        }

        self._patterns[pattern_id] = pattern
        self.logger.info(f"Created pattern: {name} (ID: {pattern_id})")

        return pattern

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a pattern by ID.

        Args:
            pattern_id: ID of the pattern to retrieve

        Returns:
            Optional[Dict[str, Any]]: Pattern data or None if not found
        """
        pattern = self._patterns.get(pattern_id)
        if not pattern:
            self.logger.warning(f"Pattern not found: {pattern_id}")
            return None

        return pattern

    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a pattern.

        Args:
            pattern_id: ID of the pattern to update
            updates: Dictionary of fields to update

        Returns:
            Optional[Dict[str, Any]]: Updated pattern data or None if not found
        """
        if pattern_id not in self._patterns:
            self.logger.warning(f"Cannot update non-existent pattern: {pattern_id}")
            return None

        pattern = self._patterns[pattern_id]

        # Update only valid fields
        valid_fields = ["name", "description", "instructions", "complexity_level", "status", "metadata"]
        for field, value in updates.items():
            if field in valid_fields:
                pattern[field] = value

        # Always update the 'updated_at' timestamp
        pattern["updated_at"] = datetime.now()

        self.logger.info(f"Updated pattern: {pattern_id}")
        return pattern

    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern.

        Args:
            pattern_id: ID of the pattern to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if pattern_id not in self._patterns:
            self.logger.warning(f"Cannot delete non-existent pattern: {pattern_id}")
            return False

        del self._patterns[pattern_id]
        self.logger.info(f"Deleted pattern: {pattern_id}")
        return True

    def list_patterns(self, status: Optional[PatternStatus] = None) -> List[Dict[str, Any]]:
        """List all patterns, optionally filtered by status.

        Args:
            status: Optional filter by pattern status

        Returns:
            List[Dict[str, Any]]: List of patterns
        """
        if status:
            return [p for p in self._patterns.values() if p["status"] == status]
        return list(self._patterns.values())

    def search_patterns(self, query: str) -> List[Dict[str, Any]]:
        """Search for patterns by name or description.

        Args:
            query: Search query string

        Returns:
            List[Dict[str, Any]]: List of matching patterns
        """
        query = query.lower()
        results = []

        for pattern in self._patterns.values():
            if (query in pattern["name"].lower() or
                    (pattern["description"] and query in pattern["description"].lower())):
                results.append(pattern)

        return results

    def add_component_to_pattern(self, pattern_id: str,
                                 component_name: str,
                                 material_type: str,
                                 dimensions: Dict[str, float],
                                 quantity: int = 1,
                                 notes: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Add a component to a pattern.

        Args:
            pattern_id: ID of the pattern
            component_name: Name of the component
            material_type: Type of material for the component
            dimensions: Component dimensions
            quantity: Number of this component needed
            notes: Optional notes about the component

        Returns:
            Optional[Dict[str, Any]]: Updated pattern or None if pattern not found
        """
        if pattern_id not in self._patterns:
            self.logger.warning(f"Cannot add component to non-existent pattern: {pattern_id}")
            return None

        pattern = self._patterns[pattern_id]

        # Create a new component
        component_id = f"CMP{len(pattern['components']) + 1:03d}"
        component = {
            "id": component_id,
            "name": component_name,
            "material_type": material_type,
            "dimensions": dimensions,
            "quantity": quantity,
            "notes": notes
        }

        pattern["components"].append(component)
        pattern["updated_at"] = datetime.now()

        self.logger.info(f"Added component {component_name} to pattern {pattern_id}")
        return pattern

    def remove_component_from_pattern(self, pattern_id: str, component_id: str) -> Optional[Dict[str, Any]]:
        """Remove a component from a pattern.

        Args:
            pattern_id: ID of the pattern
            component_id: ID of the component to remove

        Returns:
            Optional[Dict[str, Any]]: Updated pattern or None if pattern not found
        """
        if pattern_id not in self._patterns:
            self.logger.warning(f"Cannot remove component from non-existent pattern: {pattern_id}")
            return None

        pattern = self._patterns[pattern_id]

        # Find and remove the component
        for i, component in enumerate(pattern["components"]):
            if component["id"] == component_id:
                pattern["components"].pop(i)
                pattern["updated_at"] = datetime.now()
                self.logger.info(f"Removed component {component_id} from pattern {pattern_id}")
                return pattern

        self.logger.warning(f"Component {component_id} not found in pattern {pattern_id}")
        return pattern

    def change_pattern_status(self, pattern_id: str, new_status: PatternStatus) -> Optional[Dict[str, Any]]:
        """Change the status of a pattern.

        Args:
            pattern_id: ID of the pattern
            new_status: New status to set

        Returns:
            Optional[Dict[str, Any]]: Updated pattern or None if pattern not found
        """
        if pattern_id not in self._patterns:
            self.logger.warning(f"Cannot change status of non-existent pattern: {pattern_id}")
            return None

        pattern = self._patterns[pattern_id]
        old_status = pattern["status"]
        pattern["status"] = new_status
        pattern["updated_at"] = datetime.now()

        self.logger.info(f"Changed pattern {pattern_id} status from {old_status} to {new_status}")
        return pattern

    def duplicate_pattern(self, pattern_id: str, new_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Duplicate a pattern.

        Args:
            pattern_id: ID of the pattern to duplicate
            new_name: Optional name for the duplicate

        Returns:
            Optional[Dict[str, Any]]: Duplicate pattern or None if original not found
        """
        if pattern_id not in self._patterns:
            self.logger.warning(f"Cannot duplicate non-existent pattern: {pattern_id}")
            return None

        original = self._patterns[pattern_id]

        # Create new pattern with same details but new ID and name
        duplicate_id = f"PT{len(self._patterns) + 1:04d}"
        now = datetime.now()

        duplicate = {
            "id": duplicate_id,
            "name": new_name or f"Copy of {original['name']}",
            "description": original["description"],
            "instructions": original["instructions"],
            "complexity_level": original["complexity_level"],
            "status": PatternStatus.DRAFT,  # Always start as draft
            "created_at": now,
            "updated_at": now,
            "metadata": original["metadata"].copy(),
            "components": []
        }

        # Duplicate components
        for comp in original["components"]:
            duplicate["components"].append({
                "id": f"CMP{len(duplicate['components']) + 1:03d}",
                "name": comp["name"],
                "material_type": comp["material_type"],
                "dimensions": comp["dimensions"].copy(),
                "quantity": comp["quantity"],
                "notes": comp["notes"]
            })

        self._patterns[duplicate_id] = duplicate
        self.logger.info(f"Duplicated pattern {pattern_id} to {duplicate_id}")

        return duplicate