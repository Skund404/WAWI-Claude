#!/usr/bin/env python
# tests/betsy_validation/run_tests.py
"""
Script to run model validation tests for Betsy validation.
"""
import os
import sys

# Determine the project root directory
# Go up two levels from the current script's directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# Add the project root to Python path
sys.path.insert(0, project_root)

import time
import argparse
import pytest
import datetime
import logging
import subprocess
from contextlib import contextmanager

# Import circular import resolver
from utils.circular_import_resolver import get_class, register_lazy_import

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(project_root, "model_tests.log")),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("betsy_validation_tests")


@contextmanager
def timer(description):
    """Context manager for timing operations."""
    start = time.time()
    yield
    elapsed = time.time() - start
    logger.info(f"{description} completed in {elapsed:.3f} seconds")


def run_tests(args):
    """Run all tests with timing and reporting."""
    start_time = time.time()
    logger.info(f"Starting Betsy validation test suite at {datetime.datetime.now()}")

    # Specific path for Betsy validation tests
    betsy_tests_path = os.path.dirname(__file__)

    # Prepare pytest arguments
    pytest_args = [
        '-v',  # Verbose output
        '--no-header',  # No header
        '--no-summary',  # No summary
        '-xvs',  # Exit on first failure, verbose, don't capture output
        '--log-cli-level=DEBUG',  # More detailed logging
        '--tb=native',  # More detailed traceback format (changed from short)
        '--maxfail=2',  # Stop after 2 failures
    ]

    # Add filter based on arguments
    if args.performance:
        pytest_args.append("-k=TestBulkOperations or TestComplexQueries or TestEdgeCases")
    elif args.relationships:
        pytest_args.append(
            "-k=TestCustomerSalesRelationships or TestProductRelationships or TestComponentRelationships or TestProjectRelationships or TestPickingListRelationships or TestSupplierRelationships or TestInventoryRelationships")
    elif args.validation:
        pytest_args.append(
            "-k=TestRequiredFieldValidation or TestDataTypeValidation or TestEnumValidation or TestUniqueConstraintValidation or TestForeignKeyValidation or TestQuantityValidation")
    elif args.models:
        pytest_args.append(
            "-k=TestERDiagramValidation or TestModelCreation or TestModelRelationship or TestPolymorphicRelationship or TestValidationMixin or TestSoftDelete or TestCircularImport or TestDictConversion")

    # Add specific test filter if provided
    if args.test:
        pytest_args.append(f"-k={args.test}")

    # Add specific file if provided
    if args.file:
        pytest_args.append(os.path.join(betsy_tests_path, args.file))
    else:
        # If no specific file, run all tests in the directory
        pytest_args.append(betsy_tests_path)

    # Handle collect-only mode
    if args.collect_only:
        # Just collect tests to verify they can be found
        logger.info("Running pytest in collect-only mode")
        collect_args = pytest_args + ["--collect-only"]
        result = subprocess.run(
            [sys.executable, '-m', 'pytest'] + collect_args,
            capture_output=True,
            text=True,
            env=os.environ.copy(),
            cwd=project_root
        )
        if result.stdout:
            logger.info("PYTEST COLLECTION:\n" + result.stdout)
        if result.stderr:
            logger.error("PYTEST COLLECTION ERRORS:\n" + result.stderr)
        return result.returncode

    # Prepare environment for tests
    env = os.environ.copy()
    env['PYTHONPATH'] = project_root + os.pathsep + (env.get('PYTHONPATH', '') or '')

    # Log Python path and project root
    logger.debug(f"Project Root: {project_root}")
    logger.debug(f"PYTHONPATH: {env['PYTHONPATH']}")
    logger.debug(f"sys.path: {sys.path}")

    # Run tests
    try:
        with timer("Test Execution"):
            # Use subprocess to run pytest with full verbosity
            result = subprocess.run(
                [sys.executable, '-m', 'pytest'] + pytest_args,
                capture_output=True,
                text=True,
                env=env,
                cwd=project_root  # Set working directory to project root
            )

            # Log the full output
            if result.stdout:
                logger.info("PYTEST STDOUT:\n" + result.stdout)
            if result.stderr:
                logger.error("PYTEST STDERR:\n" + result.stderr)

            # Determine exit code
            exit_code = result.returncode

            logger.info(f"pytest exit code: {exit_code}")

            # Check for specific error patterns in the output
            if result.stderr and "ImportError" in result.stderr:
                logger.error("Import errors detected. This might be related to circular imports or missing modules.")
                # Extract import errors for easier debugging
                import re
                import_errors = re.findall(r'ImportError:.*', result.stderr)
                for err in import_errors:
                    logger.error(f"Import error: {err.strip()}")

            # Check for fixture errors
            if result.stderr and "fixture" in result.stderr.lower():
                logger.error("Fixture errors detected. Check if all required fixtures are defined in conftest.py.")
                # Extract fixture errors
                import re
                fixture_errors = re.findall(r'fixture.*not found', result.stderr, re.IGNORECASE)
                for err in fixture_errors:
                    logger.error(f"Fixture error: {err.strip()}")

    except Exception as e:
        logger.error(f"Test execution failed: {e}", exc_info=True)
        logger.debug("Exception details:", exc_info=True)
        exit_code = 1

    # Calculate and log total time
    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Test suite completed in {total_time:.3f} seconds")

    return exit_code


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Run Betsy validation tests')

    # Optional arguments to select specific test types
    parser.add_argument('--performance', action='store_true',
                        help='Run only performance tests')
    parser.add_argument('--relationships', action='store_true',
                        help='Run only relationship tests')
    parser.add_argument('--validation', action='store_true',
                        help='Run only validation tests')
    parser.add_argument('--models', action='store_true',
                        help='Run model base tests')
    parser.add_argument('--file', type=str,
                        help='Run tests from a specific file')
    parser.add_argument('--test', type=str,
                        help='Run a specific test by name (or part of name)')
    parser.add_argument('--collect-only', action='store_true',
                        help='Only collect tests without running them')

    args = parser.parse_args()

    try:
        return run_tests(args)
    except Exception as e:
        logger.error(f"Error in test runner: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    try:
        # Pre-execution validation
        logger.info("Verifying environment before running tests...")

        # Check that the circular import resolver is available
        try:
            from utils.circular_import_resolver import get_class, register_lazy_import

            logger.info("Circular import resolver is available.")
        except ImportError as e:
            logger.error(f"Failed to import circular_import_resolver: {e}")
            sys.exit(1)

        # Check for conftest.py
        conftest_path = os.path.join(os.path.dirname(__file__), "conftest.py")
        if not os.path.exists(conftest_path):
            logger.error(f"conftest.py not found at: {conftest_path}")
            sys.exit(1)
        logger.info(f"Found conftest.py at: {conftest_path}")

        # Execute main function
        sys.exit(main())
    except Exception as e:
        logger.error("Fatal error in test runner:", exc_info=True)
        sys.exit(1)