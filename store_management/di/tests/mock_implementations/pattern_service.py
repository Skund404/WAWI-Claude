"""
MOCK IMPLEMENTATION FOR TESTING

This is a temporary mock implementation used for testing and development.
Replace with a real implementation in the appropriate services module.

DO NOT USE IN PRODUCTION.
"""

from di.tests.mock_implementations.base_service import MockBaseService


class MockPatternService:
    """Mock implementation of IPatternService."""

    def __init__(self, session=None):
        self.session = session

    def get_all_patterns(self):
        """Get all patterns."""
        return [
            {"id": 1, "name": "[MOCK] Test Pattern 1", "skill_level": "BEGINNER"},
            {"id": 2, "name": "[MOCK] Test Pattern 2", "skill_level": "INTERMEDIATE"}
        ]

    def get_pattern_by_id(self, pattern_id):
        """Get pattern by ID."""
        return {"id": pattern_id, "name": f"[MOCK] Test Pattern {pattern_id}", "skill_level": "BEGINNER"}

    def create_pattern(self, pattern_data):
        """Create a new pattern."""
        return {"id": 999, **pattern_data, "mock_generated": True}

    def update_pattern(self, pattern_id, pattern_data):
        """Update an existing pattern."""
        return {"id": pattern_id, **pattern_data, "mock_updated": True}

    def delete_pattern(self, pattern_id):
        """Delete a pattern."""
        return True

    def get_patterns_by_skill_level(self, skill_level):
        """Get patterns by skill level."""
        return [
            {"id": 1, "name": "[MOCK] Test Pattern 1", "skill_level": skill_level}
        ]