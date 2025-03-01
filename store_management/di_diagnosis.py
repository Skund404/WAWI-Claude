# di_diagnosis.py
"""Diagnostic tool for dependency injection system."""

import importlib
import inspect
import logging
import os
import sys
from typing import Any, Dict, List, Optional, Type

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)


def run_di_diagnostics():
    """Run comprehensive diagnostics on the dependency injection system."""
    logger.info("Starting dependency injection diagnostics")

    # Ensure project root is in Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
        logger.info(f"Added project root to Python path: {project_root}")

    # Import DIDebugger
    try:
        from utils.di_debug import DIDebugger, debug_dependency_injection

        # Run full DI debugging
        container, inspection = debug_dependency_injection()

        # Specific ISupplierService diagnostics
        run_supplier_service_diagnostics()

    except ImportError:
        logger.error("Failed to import DIDebugger. Make sure utils/di_debug.py exists.")
        logger.info("Running simplified diagnostics")
        run_simplified_diagnostics()

    logger.info("Dependency injection diagnostics completed")


def run_simplified_diagnostics():
    """Run simplified diagnostics without the DIDebugger."""
    logger.info("Running simplified dependency injection diagnostics")

    try:
        # Try to import the container
        from di.container import DependencyContainer
        logger.info("Successfully imported DependencyContainer")

        # Get container instance
        container = DependencyContainer()
        logger.info("Successfully created container instance")

        # Check registrations
        logger.info(f"Container has {len(container.registrations)} direct registrations")
        logger.info(f"Container has {len(getattr(container, 'lazy_registrations', {}))} lazy registrations")

        # Try to import and resolve ISupplierService
        try:
            from services.interfaces.supplier_service import ISupplierService
            logger.info("Successfully imported ISupplierService interface")

            # Try to resolve
            try:
                supplier_service = container.get(ISupplierService)
                logger.info(f"Successfully resolved ISupplierService: {type(supplier_service).__name__}")
            except Exception as e:
                logger.error(f"Failed to resolve ISupplierService: {str(e)}")
        except ImportError as e:
            logger.error(f"Failed to import ISupplierService: {str(e)}")

        # Try to import and resolve by string
        try:
            supplier_service = container.get("ISupplierService")
            logger.info(f"Successfully resolved ISupplierService by string: {type(supplier_service).__name__}")
        except Exception as e:
            logger.error(f"Failed to resolve ISupplierService by string: {str(e)}")

        # Try to import and create supplier service directly
        try:
            from services.implementations.supplier_service import SupplierService
            logger.info("Successfully imported SupplierService implementation")

            try:
                service = SupplierService()
                logger.info(f"Successfully created SupplierService instance: {service.__class__.__name__}")

                # Try a method
                suppliers = service.get_all_suppliers()
                logger.info(f"get_all_suppliers returned {len(suppliers)} suppliers")
            except Exception as e:
                logger.error(f"Failed to create or use SupplierService: {str(e)}")
        except ImportError as e:
            logger.error(f"Failed to import SupplierService implementation: {str(e)}")

    except ImportError as e:
        logger.error(f"Failed to import DependencyContainer: {str(e)}")

    logger.info("Simplified diagnostics completed")


def run_supplier_service_diagnostics():
    """Run specific diagnostics for ISupplierService."""
    logger.info("Running specific ISupplierService diagnostics")

    # Check service interfaces module
    try:
        import services.interfaces
        logger.info(f"services.interfaces module exists: {services.interfaces.__file__}")

        # Check all available interfaces
        interfaces = [name for name in dir(services.interfaces)
                      if not name.startswith('_') and inspect.isclass(getattr(services.interfaces, name, None))]
        logger.info(f"Available interfaces in services.interfaces: {interfaces}")

        # Check supplier_service module
        try:
            import services.interfaces.supplier_service
            logger.info(f"supplier_service module exists: {services.interfaces.supplier_service.__file__}")

            # Check ISupplierService
            if hasattr(services.interfaces.supplier_service, 'ISupplierService'):
                isupplier = services.interfaces.supplier_service.ISupplierService
                logger.info(f"ISupplierService found: {isupplier.__module__}.{isupplier.__name__}")
            else:
                logger.error("ISupplierService not found in supplier_service module")

        except ImportError as e:
            logger.error(f"Failed to import supplier_service module: {str(e)}")

    except ImportError as e:
        logger.error(f"Failed to import services.interfaces module: {str(e)}")

    # Check implementation
    try:
        import services.implementations.supplier_service
        logger.info(
            f"supplier_service implementation module exists: {services.implementations.supplier_service.__file__}")

        if hasattr(services.implementations.supplier_service, 'SupplierService'):
            supplier_service = services.implementations.supplier_service.SupplierService
            logger.info(
                f"SupplierService implementation found: {supplier_service.__module__}.{supplier_service.__name__}")

            # Check inheritance
            bases = inspect.getmro(supplier_service)
            base_names = [b.__name__ for b in bases]
            logger.info(f"SupplierService inheritance: {base_names}")

            # Check if it implements ISupplierService
            from services.interfaces.supplier_service import ISupplierService
            if ISupplierService in bases:
                logger.info("SupplierService correctly implements ISupplierService")
            else:
                logger.error("SupplierService does not inherit from ISupplierService")

        else:
            logger.error("SupplierService not found in supplier_service implementation module")

    except ImportError as e:
        logger.error(f"Failed to import supplier_service implementation module: {str(e)}")

    logger.info("ISupplierService diagnostics completed")


if __name__ == "__main__":
    run_di_diagnostics()