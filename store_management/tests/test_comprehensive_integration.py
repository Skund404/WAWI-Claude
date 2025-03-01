# tests/test_comprehensive_integration.py
"""
Enhanced Comprehensive Integration Test Suite for Leatherworking Store Management Application

Covers:
- Comprehensive Workflow Testing
- Edge Case Scenarios
- Error Handling
- Performance Testing
- Concurrency Scenarios
"""

import pytest
import uuid
import concurrent.futures
import time
import random
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime, timedelta

# Import core models and exceptions
from database.models.material import Material
from database.models.project import Project
from database.models.order import Order, OrderItem
from database.models.supplier import Supplier
from database.models.hardware import Hardware
from database.models.storage import Storage
from database.models.enums import MaterialType, ProjectType, SkillLevel, OrderStatus, PaymentStatus, SupplierStatus

# Import services and interfaces
from services.interfaces.material_service import IMaterialService
from services.interfaces.project_service import IProjectService
from services.interfaces.order_service import IOrderService
from services.interfaces.supplier_service import ISupplierService
from services.interfaces.storage_service import IStorageService

# Import dependency injection and setup
from di.container import DependencyContainer
from di.setup import setup_dependency_injection

# Import error handling
from utils.error_handler import ValidationError, NotFoundError, ApplicationError


class TestEnhancedLeatherworkingIntegration:
    """
    Comprehensive and Enhanced Integration Test Suite
    """

    @pytest.fixture(scope='class')
    def dependency_container(self):
        """
        Set up dependency injection container for integration tests
        """
        container = DependencyContainer()
        setup_dependency_injection()
        return container

    @pytest.fixture(scope='function')
    def material_service(self, dependency_container):
        """
        Retrieve Material Service for testing
        """
        return dependency_container.get(IMaterialService)

    @pytest.fixture(scope='function')
    def project_service(self, dependency_container):
        """
        Retrieve Project Service for testing
        """
        return dependency_container.get(IProjectService)

    @pytest.fixture(scope='function')
    def order_service(self, dependency_container):
        """
        Retrieve Order Service for testing
        """
        return dependency_container.get(IOrderService)

    @pytest.fixture(scope='function')
    def supplier_service(self, dependency_container):
        """
        Retrieve Supplier Service for testing
        """
        return dependency_container.get(ISupplierService)

    @pytest.fixture(scope='function')
    def storage_service(self, dependency_container):
        """
        Retrieve Storage Service for testing
        """
        return dependency_container.get(IStorageService)

    # Edge Case and Error Scenario Tests
    def test_material_validation_errors(self, material_service):
        """
        Test various validation errors for material creation
        """
        # Test invalid material type
        with pytest.raises(ValidationError):
            material_service.create({
                'name': 'Invalid Material',
                'material_type': 'INVALID_TYPE',
                'quantity': -1  # Negative quantity
            })

        # Test missing required fields
        with pytest.raises(ValidationError):
            material_service.create({
                'quantity': 10.0  # Missing name and type
            })

    def test_project_edge_cases(self, project_service):
        """
        Test edge cases in project creation and management
        """
        # Test creating project with invalid skill level
        with pytest.raises(ValidationError):
            project_service.create({
                'name': 'Invalid Skill Level Project',
                'project_type': ProjectType.WALLET,
                'skill_level': 'SUPERHUMAN'
            })

        # Test project with extremely long name
        with pytest.raises(ValidationError):
            project_service.create({
                'name': 'A' * 300,  # Extremely long name
                'project_type': ProjectType.BAG
            })

    def test_order_error_scenarios(self, order_service, material_service):
        """
        Test various error scenarios in order management
        """
        # Create a material for order
        material = material_service.create({
            'name': 'Order Test Material',
            'material_type': MaterialType.LEATHER,
            'quantity': 10.0
        })

        # Test order with invalid status
        with pytest.raises(ValidationError):
            order_service.create({
                'customer_name': 'Test Customer',
                'status': 'IMPOSSIBLE_STATUS',
                'order_items': [
                    {
                        'material_id': material.id,
                        'quantity': 5.0,
                        'unit_price': 50.00
                    }
                ]
            })

        # Test order with insufficient material quantity
        with pytest.raises(ApplicationError):
            order_service.create({
                'customer_name': 'Test Customer',
                'status': OrderStatus.PENDING,
                'order_items': [
                    {
                        'material_id': material.id,
                        'quantity': 100.0,  # Far exceeds available quantity
                        'unit_price': 50.00
                    }
                ]
            })

    def test_supplier_concurrent_creation(self, supplier_service):
        """
        Test concurrent supplier creation to check for race conditions
        """

        def create_unique_supplier():
            """Create a supplier with a unique name"""
            unique_name = f"Concurrent Supplier {uuid.uuid4()}"
            return supplier_service.create({
                'name': unique_name,
                'status': SupplierStatus.ACTIVE
            })

        # Use concurrent executor to simulate multiple simultaneous creations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(create_unique_supplier) for _ in range(10)]

            # Wait for all futures to complete
            concurrent.futures.wait(futures)

            # Verify all suppliers were created successfully
            suppliers = [f.result() for f in futures]
            supplier_names = [supplier.name for supplier in suppliers]

            # Check for unique names
            assert len(set(supplier_names)) == 10, "Duplicate supplier names created"

    def test_performance_material_creation(self, material_service):
        """
        Performance test for material creation
        """
        start_time = time.time()

        # Create a large number of materials
        materials = []
        for i in range(1000):
            material = material_service.create({
                'name': f'Performance Test Material {i}',
                'material_type': random.choice(list(MaterialType)),
                'quantity': random.uniform(1.0, 100.0)
            })
            materials.append(material)

        end_time = time.time()
        creation_time = end_time - start_time

        # Assert performance threshold (adjust as needed)
        assert creation_time < 10, f"Material creation took too long: {creation_time} seconds"
        assert len(materials) == 1000, "Failed to create all materials"

    def test_complex_workflow_stress(
            self,
            material_service,
            project_service,
            order_service,
            supplier_service
    ):
        """
        Stress test simulating complex workflows with multiple operations
        """
        # Create multiple suppliers
        suppliers = [
            supplier_service.create({
                'name': f'Stress Test Supplier {i}',
                'status': SupplierStatus.ACTIVE
            }) for i in range(5)
        ]

        # Create multiple materials
        materials = [
            material_service.create({
                'name': f'Stress Test Material {i}',
                'material_type': random.choice(list(MaterialType)),
                'quantity': random.uniform(50.0, 500.0)
            }) for i in range(50)
        ]

        # Create multiple projects
        projects = []
        for i in range(20):
            project_materials = random.sample(materials, k=random.randint(1, 3))
            project = project_service.create({
                'name': f'Stress Test Project {i}',
                'project_type': random.choice(list(ProjectType)),
                'skill_level': random.choice(list(SkillLevel)),
                'materials': [m.id for m in project_materials]
            })
            projects.append(project)

        # Create multiple orders
        orders = []
        for i in range(30):
            supplier = random.choice(suppliers)
            order_materials = random.sample(materials, k=random.randint(1, 5))
            order = order_service.create({
                'customer_name': f'Stress Test Customer {i}',
                'supplier_id': supplier.id,
                'status': OrderStatus.PENDING,
                'order_items': [
                    {
                        'material_id': m.id,
                        'quantity': random.uniform(1.0, 20.0),
                        'unit_price': random.uniform(10.0, 200.0)
                    } for m in order_materials
                ]
            })
            orders.append(order)

        # Validate created entities
        assert len(suppliers) == 5
        assert len(materials) == 50
        assert len(projects) == 20
        assert len(orders) == 30

    def test_data_integrity_across_services(
            self,
            material_service,
            project_service,
            order_service
    ):
        """
        Test data integrity and relationships across different services
        """
        # Create material
        material = material_service.create({
            'name': 'Integrity Test Material',
            'material_type': MaterialType.LEATHER,
            'quantity': 100.0
        })

        # Create project using the material
        project = project_service.create({
            'name': 'Integrity Test Project',
            'project_type': ProjectType.BAG,
            'materials': [material.id]
        })

        # Create order using the material
        order = order_service.create({
            'customer_name': 'Integrity Test Customer',
            'status': OrderStatus.PENDING,
            'order_items': [
                {
                    'material_id': material.id,
                    'quantity': 50.0,
                    'unit_price': 100.00
                }
            ]
        })

        # Verify relationships
        retrieved_material = material_service.get_by_id(material.id)
        retrieved_project = project_service.get_by_id(project.id)
        retrieved_order = order_service.get_by_id(order.id)

        assert material.id in [m.id for m in retrieved_project.materials]
        assert any(item.material_id == material.id for item in retrieved_order.order_items)

    # Error Recovery and Resilience Tests
    def test_service_error_recovery(
            self,
            material_service,
            project_service
    ):
        """
        Test service error recovery and rollback mechanisms
        """
        # Attempt to create a project with an invalid material
        with pytest.raises(NotFoundError):
            project_service.create({
                'name': 'Error Recovery Project',
                'project_type': ProjectType.WALLET,
                'materials': [999999]  # Non-existent material ID
            })

        # Create a material
        material = material_service.create({
            'name': 'Recovery Test Material',
            'material_type': MaterialType.LEATHER,
            'quantity': 50.0
        })

        # Intentionally try to create an invalid project
        with pytest.raises(ValidationError):
            project_service.create({
                'name': '',  # Empty name should trigger validation error
                'project_type': ProjectType.BAG,
                'materials': [material.id]
            })


# Main execution for manual running
if __name__ == '__main__':
    pytest.main(['-v', __file__])