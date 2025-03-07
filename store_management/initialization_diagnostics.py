# initialization_diagnostics.py
"""
Advanced Diagnostics for SQLAlchemy Model Initialization Issues
"""

import importlib
import inspect
import logging
import os
import sys
import traceback
from typing import List, Dict, Any, Optional, Type

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AdvancedModelDiagnostics:
    """
    Comprehensive diagnostics for database model initialization and metadata conflicts.
    """

    def __init__(self, models_package: str = 'database.models'):
        """
        Initialize diagnostics for database models.

        Args:
            models_package: Base package for database models
        """
        self.models_package = models_package
        self.failed_modules: List[str] = []
        self.successful_modules: List[str] = []
        self.module_errors: Dict[str, str] = {}
        self.attribute_conflicts: Dict[str, List[str]] = {}

    def find_model_modules(self) -> List[str]:
        """
        Find all Python modules in the models package.

        Returns:
            List of module names
        """
        try:
            # Determine the absolute path to the models directory
            base_dir = os.path.dirname(os.path.abspath(__file__))
            models_path = os.path.join(base_dir, *self.models_package.split('.'))

            # Ensure the path exists
            if not os.path.exists(models_path):
                logger.error(f"Models directory not found: {models_path}")
                return []

            # Find all .py files that are not __init__.py or test files
            modules = [
                f[:-3] for f in os.listdir(models_path)
                if f.endswith('.py')
                   and not f.startswith('__')
                   and not f.startswith('test_')
            ]

            logger.info(f"Found {len(modules)} potential model modules")
            return modules
        except Exception as e:
            logger.error(f"Error finding model modules: {e}")
            traceback.print_exc()
            return []

    def scan_module_for_metadata_conflicts(self, module_name: str) -> Dict[str, Any]:
        """
        Deeply scan a module for potential metadata-related conflicts.

        Args:
            module_name: Name of the module to scan

        Returns:
            Dictionary of potential conflicts
        """
        full_module_name = f"{self.models_package}.{module_name}"
        conflicts = {
            'direct_metadata': [],
            'nested_metadata': [],
            'class_attributes': [],
            'parent_class_metadata': []
        }

        try:
            # Import the module
            module = importlib.import_module(full_module_name)

            # Scan all classes in the module
            for name, obj in inspect.getmembers(module):
                if inspect.isclass(obj):
                    # Check direct attributes
                    if hasattr(obj, 'metadata'):
                        conflicts['direct_metadata'].append(name)

                    # Check nested attributes
                    for attr_name, attr_value in obj.__dict__.items():
                        if attr_name == 'metadata' or 'metadata' in str(attr_value):
                            conflicts['nested_metadata'].append(f"{name}.{attr_name}")

                    # Check class attributes
                    for attr_name, attr_value in vars(obj).items():
                        if attr_name == 'metadata' or 'metadata' in str(attr_value):
                            conflicts['class_attributes'].append(f"{name}.{attr_name}")

                    # Check parent classes for metadata conflicts
                    for base in obj.__bases__:
                        if hasattr(base, 'metadata'):
                            conflicts['parent_class_metadata'].append(
                                f"{name} (inherited from {base.__name__})"
                            )

            # Remove empty conflict categories
            conflicts = {k: v for k, v in conflicts.items() if v}

            return conflicts
        except ImportError as e:
            if "cannot import name 'DeclarativeMeta'" in str(e):
                logger.warning(f"Skipping module {full_module_name} due to missing DeclarativeMeta")
                return {}
            else:
                raise
        except Exception as e:
            logger.error(f"Error scanning module {full_module_name}: {e}")
            traceback.print_exc()
            return {}

    def run_comprehensive_metadata_diagnostics(self) -> Dict[str, Any]:
        """
        Run comprehensive metadata conflict diagnostics.

        Returns:
            Detailed diagnostics report
        """
        logger.info("Starting comprehensive metadata conflict diagnostics")

        # Find all model modules
        model_modules = self.find_model_modules()

        # Diagnostics report
        diagnostics_report = {
            'total_modules': len(model_modules),
            'modules_with_metadata_conflicts': {},
            'skipped_modules': []
        }

        # Scan each module for metadata conflicts
        for module_name in model_modules:
            try:
                conflicts = self.scan_module_for_metadata_conflicts(module_name)

                if conflicts:
                    diagnostics_report['modules_with_metadata_conflicts'][module_name] = conflicts
                elif not conflicts:
                    diagnostics_report['skipped_modules'].append(module_name)
            except Exception as e:
                logger.error(f"Error processing module {module_name}: {e}")
                traceback.print_exc()

        return diagnostics_report

    def generate_detailed_report(self) -> str:
        """
        Generate a detailed report of metadata conflicts.

        Returns:
            Formatted diagnostic report as a string
        """
        # Run diagnostics
        report = self.run_comprehensive_metadata_diagnostics()

        # Format report
        report_str = [
            "METADATA CONFLICT DIAGNOSTICS REPORT",
            "=" * 50,
            f"Total Modules Scanned: {report['total_modules']}",
            f"Modules with Metadata Conflicts: {len(report['modules_with_metadata_conflicts'])}",
            f"Skipped Modules: {len(report['skipped_modules'])}",
            "\nDetailed Metadata Conflict Analysis:",
            *self._format_conflict_details(report['modules_with_metadata_conflicts']),
            "\nSkipped Modules:",
            *report['skipped_modules']
        ]

        return "\n".join(report_str)

    def _format_conflict_details(self, conflicts: Dict[str, Dict]) -> List[str]:
        """
        Format detailed conflict information.

        Args:
            conflicts: Dictionary of metadata conflicts

        Returns:
            List of formatted conflict strings
        """
        formatted_conflicts = []
        for module, conflict_types in conflicts.items():
            formatted_conflicts.append(f"\nModule: {module}")
            for conflict_type, items in conflict_types.items():
                formatted_conflicts.append(f"  {conflict_type.replace('_', ' ').title()}:")
                for item in items:
                    formatted_conflicts.append(f"    - {item}")

        return formatted_conflicts if formatted_conflicts else ["No metadata conflicts detected."]


def main():
    """
    Main entry point for running advanced metadata diagnostics.
    """
    diagnostics = AdvancedModelDiagnostics()

    try:
        # Run diagnostics
        report = diagnostics.generate_detailed_report()

        # Print report
        print(report)

        # Write report to file
        log_file = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            'advanced_metadata_diagnostics.log'
        )
        with open(log_file, 'w') as f:
            f.write(report)

        logger.info(f"Diagnostics completed. Check {log_file} for details.")

    except Exception as e:
        logger.error(f"Critical error during diagnostics: {e}")
        traceback.print_exc()


if __name__ == '__main__':
    main()