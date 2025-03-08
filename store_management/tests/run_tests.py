#!/usr/bin/env python
# tests/run_tests.py
"""
Script to run model validation tests in a specific order,
with detailed reporting and timing information.
"""
# At the top of run_tests.py (before any imports)
import os
import sys

# Add the project root directory to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

import os
import sys
import time
import argparse
import unittest
import pytest
import datetime
import logging
from contextlib import contextmanager

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("model_tests.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger("model_test_runner")


@contextmanager
def timer(description):
    """Context manager for timing operations."""
    start = time.time()
    yield
    elapsed = time.time() - start
    logger.info(f"{description} completed in {elapsed:.3f} seconds")


def setup_database():
    """Set up test database."""
    from database.models.base import Base, initialize_all_model_relationships
    from sqlalchemy import create_engine

    logger.info("Setting up test database...")

    # Create an in-memory SQLite database
    engine = create_engine('sqlite:///:memory:', echo=False)

    # Create all tables
    Base.metadata.create_all(engine)

    # Initialize relationships
    initialize_all_model_relationships()

    logger.info("Database setup completed")
    return engine


def run_tests(args):
    """Run all tests with timing and reporting."""
    start_time = time.time()
    logger.info(f"Starting model validation test suite at {datetime.datetime.now()}")

    if args.setup_only:
        # Just set up the database to test initialization
        with timer("Database initialization"):
            engine = setup_database()

            # Log registered models
            from database.models.base import Base
            models = Base.list_models()
            logger.info(f"Registered models: {', '.join(models)}")

        logger.info("Database setup test completed successfully")
        return

    # Run the tests
    if args.unittest:
        # Run with unittest
        with timer("unittest tests"):
            test_suite = unittest.defaultTestLoader.discover('tests', pattern='test_*.py')
            test_runner = unittest.TextTestRunner(verbosity=2)
            result = test_runner.run(test_suite)

            logger.info(f"unittest results: {result.testsRun} tests run, "
                        f"{len(result.errors)} errors, {len(result.failures)} failures")
    else:
        # Run with pytest
        with timer("pytest tests"):
            args_list = [
                '-v',  # Verbose output
                '--no-header',  # No header
                '--no-summary',  # No summary
                '-xvs',  # Exit on first failure, verbose, don't capture output
            ]

            if args.performance:
                args_list.append('tests/test_model_performance.py')
            elif args.relationships:
                args_list.append('tests/test_model_relationships.py')
            elif args.validation:
                args_list.append('tests/test_model_validation.py')
            else:
                args_list.append('tests')  # Run all tests

            exit_code = pytest.main(args_list)

            logger.info(f"pytest exit code: {exit_code}")

    end_time = time.time()
    total_time = end_time - start_time
    logger.info(f"Test suite completed in {total_time:.3f} seconds")


def main():
    """Main entry point for the test runner."""
    parser = argparse.ArgumentParser(description='Run model validation tests')
    parser.add_argument('--setup-only', action='store_true', help='Only test database setup')
    parser.add_argument('--unittest', action='store_true', help='Run with unittest instead of pytest')
    parser.add_argument('--performance', action='store_true', help='Run only performance tests')
    parser.add_argument('--relationships', action='store_true', help='Run only relationship tests')
    parser.add_argument('--validation', action='store_true', help='Run only validation tests')

    args = parser.parse_args()

    try:
        run_tests(args)
    except Exception as e:
        logger.error(f"Error running tests: {e}", exc_info=True)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())