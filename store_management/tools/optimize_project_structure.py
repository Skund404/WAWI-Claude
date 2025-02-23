#!/usr/bin/env python3
"""
/tools/optimize_project_structure.py

A comprehensive script to analyze and fix various structural issues in the store_management project.
This script handles:
1. Service consolidation
2. Repository standardization
3. Error handling improvement
4. Configuration centralization
5. Type hint addition
6. Logging standardization

Author: Project Optimization Team
Date: 2024-02-24
"""

import os
import sys
import ast
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceInfo:
    """Information about a service implementation."""
    name: str
    path: Path
    methods: Set[str]
    dependencies: Set[str]
    interface_path: Optional[Path] = None


@dataclass
class RepositoryInfo:
    """Information about a repository implementation."""
    name: str
    path: Path
    entity_type: str
    methods: Set[str]


class ProjectOptimizer:
    """Handles project-wide optimization and fixes."""

    def __init__(self, project_root: Path):
        """
        Initialize the project optimizer.

        Args:
            project_root: Path to the project root directory
        """
        self.project_root = project_root
        self.services: Dict[str, ServiceInfo] = {}
        self.repositories: Dict[str, RepositoryInfo] = {}
        self.config_files: List[Path] = []
        self.type_hint_needed: List[Path] = []

    def analyze_project(self) -> None:
        """Perform complete project analysis."""
        logger.info("Starting project analysis...")

        try:
            self._find_services()
            self._find_repositories()
            self._analyze_configurations()
            self._check_type_hints()
            logger.info("Project analysis completed successfully")
        except Exception as e:
            logger.error(f"Error during project analysis: {e}")
            raise

    def _find_services(self) -> None:
        """Locate and analyze all service implementations."""
        service_dir = self.project_root / "services"
        impl_dir = service_dir / "implementations"

        for service_file in impl_dir.glob("**/*.py"):
            try:
                with open(service_file, 'r') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if node.name.endswith('Service'):
                            methods = {
                                n.name for n in node.body
                                if isinstance(n, ast.FunctionDef)
                            }
                            self.services[node.name] = ServiceInfo(
                                name=node.name,
                                path=service_file,
                                methods=methods,
                                dependencies=self._extract_dependencies(node)
                            )
            except Exception as e:
                logger.error(f"Error analyzing service file {service_file}: {e}")

    def _find_repositories(self) -> None:
        """Locate and analyze all repository implementations."""
        repo_dir = self.project_root / "database" / "repositories"

        for repo_file in repo_dir.glob("**/*.py"):
            try:
                with open(repo_file, 'r') as f:
                    tree = ast.parse(f.read())

                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        if node.name.endswith('Repository'):
                            self.repositories[node.name] = RepositoryInfo(
                                name=node.name,
                                path=repo_file,
                                entity_type=self._extract_entity_type(node),
                                methods=self._extract_methods(node)
                            )
            except Exception as e:
                logger.error(f"Error analyzing repository file {repo_file}: {e}")

    def optimize_services(self) -> None:
        """Consolidate and optimize service implementations."""
        logger.info("Optimizing service layer...")

        # Group services by functionality
        service_groups = self._group_similar_services()

        for group in service_groups:
            try:
                self._consolidate_service_group(group)
            except Exception as e:
                logger.error(f"Error consolidating service group: {e}")

    def standardize_repositories(self) -> None:
        """Standardize repository implementations."""
        logger.info("Standardizing repositories...")

        base_repo_template = self._create_base_repository_template()

        for repo in self.repositories.values():
            try:
                self._update_repository(repo, base_repo_template)
            except Exception as e:
                logger.error(f"Error standardizing repository {repo.name}: {e}")

    def centralize_configuration(self) -> None:
        """Centralize configuration management."""
        logger.info("Centralizing configuration...")

        config_dir = self.project_root / "config"
        new_config = config_dir / "configuration.py"

        try:
            self._merge_configurations(new_config)
            self._update_config_imports()
        except Exception as e:
            logger.error(f"Error centralizing configuration: {e}")

    def add_type_hints(self) -> None:
        """Add type hints to files that need them."""
        logger.info("Adding type hints...")

        for file_path in self.type_hint_needed:
            try:
                self._add_file_type_hints(file_path)
            except Exception as e:
                logger.error(f"Error adding type hints to {file_path}: {e}")

    def standardize_error_handling(self) -> None:
        """Implement consistent error handling."""
        logger.info("Standardizing error handling...")

        error_handler = self._create_error_handler()

        try:
            self._implement_error_handling(error_handler)
        except Exception as e:
            logger.error(f"Error standardizing error handling: {e}")

    def _extract_dependencies(self, node: ast.ClassDef) -> Set[str]:
        """Extract service dependencies from class definition."""
        dependencies = set()

        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                if n.func.id.endswith('Service'):
                    dependencies.add(n.func.id)

        return dependencies

    def _extract_entity_type(self, node: ast.ClassDef) -> str:
        """Extract the entity type handled by a repository."""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id.endswith('Repository'):
                return base.id.replace('Repository', '')
        return 'Unknown'

    def _extract_methods(self, node: ast.ClassDef) -> Set[str]:
        """Extract method names from a class definition."""
        return {
            n.name for n in node.body
            if isinstance(n, ast.FunctionDef)
        }

    def _group_similar_services(self) -> List[List[ServiceInfo]]:
        """Group services with similar functionality."""
        groups = []
        processed = set()

        for service_name, service_info in self.services.items():
            if service_name in processed:
                continue

            similar_services = [service_info]
            processed.add(service_name)

            for other_name, other_info in self.services.items():
                if other_name not in processed:
                    if self._are_services_similar(service_info, other_info):
                        similar_services.append(other_info)
                        processed.add(other_name)

            groups.append(similar_services)

        return groups

    def _are_services_similar(self, service1: ServiceInfo, service2: ServiceInfo) -> bool:
        """Determine if two services have similar functionality."""
        # Check method name similarity
        method_similarity = len(service1.methods & service2.methods) / \
                            len(service1.methods | service2.methods)

        # Check dependency similarity
        dep_similarity = len(service1.dependencies & service2.dependencies) / \
                         len(service1.dependencies | service2.dependencies) \
            if service1.dependencies or service2.dependencies else 1.0

        return method_similarity > 0.7 and dep_similarity > 0.6

    def run(self) -> None:
        """Execute all optimization steps."""
        try:
            logger.info("Starting project optimization...")

            # Create backup
            self._create_backup()

            # Run optimization steps
            self.analyze_project()
            self.optimize_services()
            self.standardize_repositories()
            self.centralize_configuration()
            self.add_type_hints()
            self.standardize_error_handling()

            logger.info("Project optimization completed successfully")

        except Exception as e:
            logger.error(f"Error during optimization: {e}")
            self._restore_backup()
            raise

    def _create_backup(self) -> None:
        """Create a backup of the project."""
        backup_dir = self.project_root.parent / f"{self.project_root.name}_backup"
        shutil.copytree(self.project_root, backup_dir)
        logger.info(f"Created backup at {backup_dir}")

    def _restore_backup(self) -> None:
        """Restore project from backup if optimization fails."""
        backup_dir = self.project_root.parent / f"{self.project_root.name}_backup"
        if backup_dir.exists():
            shutil.rmtree(self.project_root)
            shutil.move(backup_dir, self.project_root)
            logger.info("Restored project from backup")


def main() -> None:
    """Main entry point for the optimization script."""
    try:
        # Get project root
        project_root = Path(__file__).resolve().parent.parent

        # Create and run optimizer
        optimizer = ProjectOptimizer(project_root)
        optimizer.run()

    except Exception as e:
        logger.error(f"Optimization failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()