#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: tests/models/test_projects_components.py

import unittest
from datetime import datetime
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from models import (
    Base, Project, ProjectComponent, Component,
    ComponentMaterial, Material, Pattern,
    ProjectType, ProjectStatus, ComponentType, SkillLevel
)


class TestProjectModel(unittest.TestCase):
    """Test the Project model implementation against ER diagram specifications."""

    @classmethod
    def setUpClass(cls):
        cls.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(cls.engine)
        cls.Session = sessionmaker(bind=cls.engine)
        cls.session = cls.Session()

    @classmethod
    def tearDownClass(cls):
        cls.session.close()
        Base.metadata.drop_all(cls.engine)

    def test_project_schema(self):
        """Test that Project model has all required columns from ER diagram."""
        inspector = inspect(self.engine)
        columns = {col['name'] for col in inspector.get_columns('projects')}

        required_columns = {
            'id', 'name', 'description', 'type', 'status',
            'start_date', 'end_date', 'estimated_hours',
            'actual_hours', 'notes', 'sales_id',
            'created_at', 'updated_at'
        }
        for col in required_columns:
            self.assertIn(col, columns, f"Column {col} should exist in Project model")

    def test_project_relationships(self):
        """Test project relationships match ER diagram."""
        project = Project(
            name="Test Project",
            description="Test project description",
            type=ProjectType.WALLET,
            status=ProjectStatus.PLANNED
        )
        self.session.add(project)
        self.session.commit()

        # Verify relationship attributes exist
        self.assertTrue(hasattr(project, 'sale'), "Project should have 'sale' relationship")
        self.assertTrue(hasattr(project, 'project_components'), "Project should have 'project_components' relationship")
        self.assertTrue(hasattr(project, 'tool_lists'), "Project should have 'tool_lists' relationship")

    def test_project_status_update(self):
        """Test project status update functionality."""
        project = Project(
            name="Status Test Project",
            description="Testing status transitions",
            type=ProjectType.BELT,
            status=ProjectStatus.PLANNED
        )
        self.session.add(project)
        self.session.commit()

        # Initial state
        self.assertIsNone(project.start_date)
        self.assertIsNone(project.end_date)

        # Update to in progress
        project.update_status(ProjectStatus.IN_PROGRESS)
        self.assertIsNotNone(project.start_date)
        self.assertIsNone(project.end_date)

        # Update to completed
        project.update_status(ProjectStatus.COMPLETED)
        self.assertIsNotNone(project.start_date)
        self.assertIsNotNone(project.end_date)

# Additional test classes for Component, ComponentMaterial, Pattern would follow...
# (Truncated for brevity)