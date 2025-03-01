# utils/di_debug.py
"""Debugging utilities for dependency injection system."""

import inspect
import logging
import sys
from typing import Any, Dict, List, Optional, Set, Type

from di.container import DependencyContainer

logger = logging.getLogger(__name__)


class DIDebugger:
    """Debugging tool for the dependency injection container."""

    @classmethod
    def inspect_container(cls, container: Optional[DependencyContainer] = None) -> Dict[str, Any]:
        """
        Inspect the dependency injection container and return detailed information.

        Args:
            container: The container to inspect, or the default if None

        Returns:
            Dict with container inspection results
        """
        if container is None:
            container = DependencyContainer()

        result = {
            "registrations": {},
            "lazy_registrations": {},
            "resolution_failures": [],
            "service_details": {}
        }

        # Copy registrations and lazy registrations
        for name, impl in container.registrations.items():
            result["registrations"][name] = {
                "type": type(impl).__name__,
                "callable": callable(impl),
                "instance": not callable(impl),
                "module": getattr(impl, "__module__", "unknown")
            }

        for name, (module_path, class_name) in container.lazy_registrations.items():
            result["lazy_registrations"][name] = {
                "module_path": module_path,
                "class_name": class_name
            }

        # Try to resolve all registered services
        for name in list(container.registrations.keys()) + list(container.lazy_registrations.keys()):
            try:
                service = container.get(name)
                if service:
                    result["service_details"][name] = {
                        "resolved": True,
                        "type": type(service).__name__,
                        "module": service.__class__.__module__,
                        "methods": [m for m in dir(service) if not m.startswith("_") and callable(getattr(service, m))]
                    }
            except Exception as e:
                result["resolution_failures"].append({
                    "service": name,
                    "error": str(e),
                    "error_type": type(e).__name__
                })

        return result

    @classmethod
    def print_container_status(cls, container: Optional[DependencyContainer] = None) -> None:
        """
        Print detailed status of the dependency injection container.

        Args:
            container: The container to inspect, or the default if None
        """
        inspection = cls.inspect_container(container)

        print("\n=== DEPENDENCY INJECTION CONTAINER STATUS ===")

        print("\n== Registered Services ==")
        for name, details in inspection["registrations"].items():
            status = "✓ Instance" if details["instance"] else "✓ Factory" if details["callable"] else "? Unknown"
            print(f"  {status} | {name} ({details['module']})")

        print("\n== Lazy Registered Services ==")
        for name, details in inspection["lazy_registrations"].items():
            print(f"  ⋯ Lazy | {name} ({details['module_path']}.{details['class_name']})")

        if inspection["resolution_failures"]:
            print("\n== Resolution Failures ==")
            for failure in inspection["resolution_failures"]:
                print(f"  ✗ {failure['service']}: {failure['error_type']} - {failure['error']}")

        print("\n== Successfully Resolved Services ==")
        resolved = {name: details for name, details in inspection["service_details"].items()
                    if details.get("resolved", False)}
        if resolved:
            for name, details in resolved.items():
                print(f"  ✓ {name} ({details['module']}.{details['type']})")
                print(
                    f"    Available methods: {', '.join(details['methods'][:5])}{'...' if len(details['methods']) > 5 else ''}")
        else:
            print("  No services could be resolved")

        print("\n=============================================")


def debug_dependency_injection():
    """Run comprehensive debugging on the dependency injection setup."""
    from di.setup import setup_dependency_injection

    logger.info("Starting dependency injection debugging")

    try:
        # Set up container
        container = setup_dependency_injection()

        # Print container status
        DIDebugger.print_container_status(container)

        # Detailed logging
        inspection = DIDebugger.inspect_container(container)

        logger.info(f"Container has {len(inspection['registrations'])} direct registrations")
        logger.info(f"Container has {len(inspection['lazy_registrations'])} lazy registrations")

        if inspection["resolution_failures"]:
            logger.error(f"Found {len(inspection['resolution_failures'])} resolution failures:")
            for failure in inspection["resolution_failures"]:
                logger.error(f"  Failed to resolve {failure['service']}: {failure['error']}")

        return container, inspection

    except Exception as e:
        logger.error(f"Critical error during dependency injection debugging: {e}")
        return None, {"error": str(e), "error_type": type(e).__name__}


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    debug_dependency_injection()