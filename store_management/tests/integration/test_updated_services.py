"""
tests/integration/test_updated_services.py
Comprehensive integration tests for project component service.
"""
import unittest
from unittest.mock import MagicMock, patch

from sqlalchemy.orm import Session, joinedload

from database.models.components import ProjectComponent, Component
from database.models.project import Project
from database.sqlalchemy.session import get_db_session

from services.base_service import (
    NotFoundError,
    ValidationError,
    ServiceError
)
from services.implementations.project_component_service import ProjectComponentService

# Import PickingListItem separately to avoid circular import issues
from database.models.picking_list import PickingListItem


class TestProjectComponentService(unittest.TestCase):
    """
    Comprehensive test suite for ProjectComponentService.
    Covers all major functionality and error scenarios.
    """

    def setUp(self):
        """
        Set up test environment with mocked dependencies.
        """
        # Create mock session and repository
        self.session = MagicMock(spec=Session)
        self.project_repo = MagicMock()

        # Instantiate service with mocked dependencies
        self.service = ProjectComponentService(self.project_repo)
        self.service.session = self.session

        # Patch SQLAlchemy internals to prevent relationship resolution
        self._patch_sqlalchemy_internals()

    def _patch_sqlalchemy_internals(self):
        """
        Patch SQLAlchemy internals to prevent relationship resolution and recursion.
        """
        def mock_entity_property(self):
            """Mock entity property to prevent recursion."""
            return self

        def mock_strategy_options(*args, **kwargs):
            """Mock strategy options to return a no-op object."""
            mock_options = MagicMock()
            mock_options.__getattr__.return_value = mock_options
            return mock_options

        # Patch various SQLAlchemy internals
        patches = [
            patch('sqlalchemy.orm.relationships.RelationshipProperty.entity',
                  create=True, new_callable=property, side_effect=mock_entity_property),
            patch('sqlalchemy.orm.strategy_options.Load.joinedload',
                  side_effect=mock_strategy_options),
            patch('sqlalchemy.orm.strategy_options._generate_from_keys',
                  return_value=MagicMock()),
        ]

        # Start and store patches for cleanup
        self._sqlalchemy_patches = [p.start() for p in patches]
        self.addCleanup(self._stop_sqlalchemy_patches)

    def _stop_sqlalchemy_patches(self):
        """
        Stop all SQLAlchemy patches.
        """
        for patch in self._sqlalchemy_patches:
            patch.stop()

    def _create_mock_project_component(self, **kwargs):
        """
        Create a mock ProjectComponent with default or provided attributes.

        Args:
            **kwargs: Override default attributes

        Returns:
            MagicMock of ProjectComponent
        """
        default_attrs = {
            'id': 1,
            'project_id': 100,
            'component_id': 200,
            'quantity': 1,
            'picking_list_item_id': None,
            'name': 'Test Component',
            'type': 'project_component'
        }
        default_attrs.update(kwargs)

        # Create a MagicMock with specific attributes
        mock_component = MagicMock(spec=ProjectComponent)

        # Set all attributes directly
        for key, value in default_attrs.items():
            setattr(mock_component, key, value)

        # Add mock related objects
        mock_related_project = MagicMock(spec=Project)
        mock_related_project.id = 100
        mock_related_project.name = 'Test Project'

        mock_base_component = MagicMock(spec=Component)
        mock_base_component.id = 200
        mock_base_component.name = 'Base Component'

        # Configure relationships as mocked attributes
        mock_component.project = mock_related_project
        mock_component.component = mock_base_component

        # Optional picking list item relationship
        if default_attrs.get('picking_list_item_id') is not None:
            mock_picking_list_item = MagicMock(spec=PickingListItem)
            mock_picking_list_item.id = default_attrs['picking_list_item_id']
            mock_component.picking_list_item = mock_picking_list_item

        return mock_component

    def test_create_component_success(self):
        """
        Test successful creation of a project component.
        """
        # Setup mocks
        mock_project = MagicMock(id=100)
        mock_component = MagicMock(id=200)

        # Configure repository and session mocks
        self.project_repo.get_by_id.return_value = mock_project

        # Configure query mock for component
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_component
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        # Patch ProjectComponent creation
        with patch('database.models.components.ProjectComponent') as mock_project_component_class:
            mock_created_component = self._create_mock_project_component(
                project_id=100, component_id=200, quantity=3
            )
            mock_project_component_class.return_value = mock_created_component

            # Call method
            result = self.service.create_component(
                project_id=100,
                component_id=200,
                quantity=3
            )

        # Assertions
        self.session.add.assert_called_once()
        self.session.commit.assert_called_once()

        # Verify returned data
        self.assertIsNotNone(result)
        self.assertEqual(result['project_id'], 100)
        self.assertEqual(result['component_id'], 200)
        self.assertEqual(result['quantity'], 3)

    def test_create_component_invalid_quantity(self):
        """
        Test component creation fails with invalid quantity.
        """
        with self.assertRaises(ValidationError):
            self.service.create_component(
                project_id=100,
                component_id=200,
                quantity=0
            )

    def test_create_component_nonexistent_project(self):
        """
        Test component creation fails for nonexistent project.
        """
        # Configure project repository to return None
        self.project_repo.get_by_id.return_value = None

        with self.assertRaises(NotFoundError):
            self.service.create_component(
                project_id=999,
                component_id=200,
                quantity=1
            )

    def test_create_component_nonexistent_component(self):
        """
        Test component creation fails for nonexistent component.
        """
        # Setup mock project
        mock_project = MagicMock(id=100)
        self.project_repo.get_by_id.return_value = mock_project

        # Configure query mock to return None for component
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        with self.assertRaises(NotFoundError):
            self.service.create_component(
                project_id=100,
                component_id=999,
                quantity=1
            )

    def test_get_component_success(self):
        """
        Test successfully retrieving a project component.
        """
        # Create mock project component with related entities
        mock_project_component = self._create_mock_project_component()

        # Disable default behavior of joinedload
        mock_options = MagicMock()
        mock_options.options.return_value = mock_options

        # Configure session query mock
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project_component
        mock_query.options.return_value = mock_options
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        # Call method
        result = self.service.get_component(1)

        # Assertions
        self.assertIsNotNone(result)
        self.assertEqual(result['id'], 1)
        self.assertEqual(result['project_id'], 100)
        self.assertEqual(result['component_id'], 200)

    def test_get_component_not_found(self):
        """
        Test retrieving a nonexistent project component.
        """
        # Disable default behavior of joinedload
        mock_options = MagicMock()
        mock_options.options.return_value = mock_options

        # Configure session query mock to return None
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.options.return_value = mock_options
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        # Expect NotFoundError
        with self.assertRaises(NotFoundError):
            self.service.get_component(999)

    def test_link_to_picking_list_item_success(self):
        """
        Test successfully linking a project component to a picking list item.
        """
        # Create mock project component and picking list item
        mock_project_component = self._create_mock_project_component(
            picking_list_item_id=None
        )
        mock_picking_list_item = MagicMock(spec=PickingListItem, id=301)

        # Configure session query mocks
        # For project component
        mock_pc_query = MagicMock()
        mock_pc_filter = MagicMock()
        mock_pc_filter.first.return_value = mock_project_component
        mock_pc_query.filter.return_value = mock_pc_filter

        # For picking list item
        mock_pli_query = MagicMock()
        mock_pli_filter = MagicMock()
        mock_pli_filter.first.return_value = mock_picking_list_item

        # Configure side effect for queries
        self.session.query.side_effect = [
            mock_pc_query,
            mock_pli_query
        ]

        # Call method
        result = self.service.link_to_picking_list_item(
            project_component_id=1,
            picking_list_item_id=301
        )

        # Assertions
        self.session.commit.assert_called_once()
        self.assertEqual(result['picking_list_item_id'], 301)

    def test_link_to_picking_list_item_already_linked(self):
        """
        Test linking a project component that's already linked.
        """
        # Create mock project component already linked
        mock_project_component = self._create_mock_project_component(
            picking_list_item_id=100
        )

        # Configure session query mock
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project_component
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        # Expect ValidationError
        with self.assertRaises(ValidationError):
            self.service.link_to_picking_list_item(
                project_component_id=1,
                picking_list_item_id=301
            )

    def test_update_quantity_success(self):
        """
        Test successfully updating a project component's quantity.
        """
        # Create mock project component
        mock_project_component = self._create_mock_project_component()

        # Configure session query mock
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = mock_project_component
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        # Call method
        result = self.service.update_quantity(
            project_component_id=1,
            quantity=5
        )

        # Assertions
        self.session.commit.assert_called_once()
        self.assertEqual(result['quantity'], 5)

    def test_update_quantity_invalid_input(self):
        """
        Test updating quantity fails with invalid input.
        """
        with self.assertRaises(ValidationError):
            self.service.update_quantity(
                project_component_id=1,
                quantity=0
            )

    def test_update_quantity_nonexistent_component(self):
        """
        Test updating quantity for nonexistent project component fails.
        """
        # Configure query mock to return None
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = None
        mock_query.filter.return_value = mock_filter
        self.session.query.return_value = mock_query

        # Expect NotFoundError
        with self.assertRaises(NotFoundError):
            self.service.update_quantity(
                project_component_id=999,
                quantity=5
            )


if __name__ == '__main__':
    unittest.main()