#!/usr/bin/env python3

"""
A comprehensive script to verify project structure fixes.
This script validates:
1. Log centralization
2. Backup consolidation
3. Service consolidation
4. Configuration standardization
5. Code cleanup

Author: Project Optimization Team
Date: 2024-02-24
"""

import os
import sys
import logging
import shutil
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
import re
import ast
import time


class LogManager:
    """Manages log file handling and centralization."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logs_dir = project_root / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        self.temp_log = project_root / 'temp_verification.log'

        # Configure logging
        self.file_handler = logging.FileHandler(self.temp_log)
        self.console_handler = logging.StreamHandler(sys.stdout)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[self.file_handler, self.console_handler]
        )

        self.logger = logging.getLogger(__name__)

    def cleanup_and_centralize(self) -> None:
        """Cleanup logging and move logs to centralized location."""
        # Close the file handler to release the file
        self.file_handler.close()
        logging.getLogger().removeHandler(self.file_handler)

        # Now move the log files
        log_files = [
            ('temp_verification.log', 'tool_verification.log'),
            ('fix_verification.log', 'tool_fix_verification.log'),
            ('project_fixes.log', 'tool_project_fixes.log')
        ]

        for src_name, dst_name in log_files:
            src = self.project_root / src_name
            if src.exists():
                try:
                    dst = self.logs_dir / dst_name
                    shutil.move(str(src), str(dst))
                    print(f"Moved {src_name} to logs directory")
                except Exception as e:
                    print(f"Error moving {src_name}: {e}")


@dataclass
class VerificationResult:
    """Results of a verification check."""
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class FixVerifier:
    """Verifies that project fixes were applied correctly."""

    def __init__(self, project_root: Path):
        """Initialize the verifier with project root path."""
        self.project_root = Path(project_root)
        self.results: Dict[str, VerificationResult] = {}
        self.logs_dir = self.project_root / 'logs'
        self.backups_dir = self.project_root / 'backups'
        self.logs_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        self.log_manager = LogManager(project_root)
        self.logger = logging.getLogger(__name__)

    def verify_all(self) -> bool:
        """Run all verifications and return overall success."""
        self.logger.info("Starting fix verification...")

        try:
            # Run all verifications
            self.verify_log_centralization()
            self.verify_backup_consolidation()
            self.verify_service_consolidation()
            self.verify_config_standardization()
            self.verify_code_cleanup()

            # Generate report
            self._generate_report()

            # Move logs to centralized location
            self.log_manager.cleanup_and_centralize()

            # Check overall success
            all_passed = all(result.passed for result in self.results.values())
            status = 'completed successfully' if all_passed else 'found issues'
            print(f"Verification {status}")

            return all_passed

        except Exception as e:
            self.logger.error(f"Error during verification: {e}")
            return False

    def verify_log_centralization(self) -> None:
        """Verify that all logs are in the centralized logs directory."""
        self.logger.info("Verifying log centralization...")

        scattered_logs = []
        # Exclude our temporary verification log
        for log_file in self.project_root.rglob("*.log"):
            if log_file.name == 'temp_verification.log':
                continue
            if 'logs' not in str(log_file.parent).split(os.sep):
                scattered_logs.append(str(log_file))

        self.results['log_centralization'] = VerificationResult(
            passed=len(scattered_logs) == 0,
            message="All logs are centralized" if len(scattered_logs) == 0
            else "Found scattered log files",
            details={'scattered_logs': scattered_logs}
        )

    def verify_backup_consolidation(self) -> None:
        """Verify that all backups are in the centralized backup directory."""
        self.logger.info("Verifying backup consolidation...")

        scattered_backups = []
        for pattern in ['*.bak', '*.backup', '*_backup_*']:
            for backup_file in self.project_root.rglob(pattern):
                if 'backups' not in str(backup_file.parent).split(os.sep):
                    scattered_backups.append(str(backup_file))

        self.results['backup_consolidation'] = VerificationResult(
            passed=len(scattered_backups) == 0,
            message="All backups are consolidated" if len(scattered_backups) == 0
            else "Found scattered backup files",
            details={'scattered_backups': scattered_backups}
        )

    def verify_service_consolidation(self) -> None:
        """Verify service implementation consolidation."""
        self.logger.info("Verifying service consolidation...")

        services_dir = self.project_root / 'services'
        implementations_dir = services_dir / 'implementations'
        issues = []

        # Check for service files outside implementations directory
        if services_dir.exists():
            for service_file in services_dir.glob("*_service.py"):
                if service_file.parent == services_dir:
                    issues.append(f"Service file outside implementations: {service_file}")

            # Check for duplicate implementations
            impl_map: Dict[str, List[Path]] = {}
            if implementations_dir.exists():
                for impl_file in implementations_dir.rglob("*.py"):
                    if impl_file.name == "__init__.py":
                        continue
                    base_name = impl_file.stem.replace('_service', '')
                    if base_name not in impl_map:
                        impl_map[base_name] = []
                    impl_map[base_name].append(impl_file)

                for base_name, impls in impl_map.items():
                    if len(impls) > 1:
                        issues.append(
                            f"Multiple implementations for {base_name}: "
                            f"{[str(p) for p in impls]}"
                        )

        self.results['service_consolidation'] = VerificationResult(
            passed=len(issues) == 0,
            message="Services are properly consolidated" if len(issues) == 0
            else "Found service consolidation issues",
            details={'issues': issues}
        )

    def verify_config_standardization(self) -> None:
        """Verify configuration standardization."""
        self.logger.info("Verifying configuration standardization...")

        issues = []
        config_dir = self.project_root / 'config'

        if not config_dir.exists():
            issues.append("Config directory not found")
        else:
            # Check for centralized configuration
            central_config = config_dir / 'configuration.py'
            if not central_config.exists():
                issues.append("Missing centralized configuration file")
            else:
                # Verify configuration content
                try:
                    with open(central_config, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read())

                    # Check for Configuration class
                    has_config_class = any(
                        isinstance(node, ast.ClassDef) and
                        node.name == 'Configuration'
                        for node in ast.walk(tree)
                    )

                    if not has_config_class:
                        issues.append("configuration.py missing Configuration class")

                except Exception as e:
                    issues.append(f"Error analyzing configuration.py: {e}")

        self.results['config_standardization'] = VerificationResult(
            passed=len(issues) == 0,
            message="Configuration is properly standardized" if len(issues) == 0
            else "Found configuration issues",
            details={'issues': issues}
        )

    def verify_code_cleanup(self) -> None:
        """Verify code cleanup and syntax fixes."""
        self.logger.info("Verifying code cleanup...")

        issues = []

        # Check for redundant paths
        redundant_paths = [
            self.project_root / "path",
            self.project_root / "database/sqlalchemy/path"
        ]

        for path in redundant_paths:
            if path.exists():
                issues.append(f"Redundant path still exists: {path}")

        # Check specific files for syntax
        to_check = {
            'database/sqlalchemy/mixins/validation_mixing.py': self._check_validation_mixing,
            'pyproject.toml.py': self._check_pyproject_toml
        }

        for rel_path, check_func in to_check.items():
            full_path = self.project_root / rel_path
            if full_path.exists():
                try:
                    result = check_func(full_path)
                    if not result:
                        issues.append(f"Syntax check failed for {rel_path}")
                except Exception as e:
                    issues.append(f"Error checking {rel_path}: {e}")

        self.results['code_cleanup'] = VerificationResult(
            passed=len(issues) == 0,
            message="Code cleanup is complete" if len(issues) == 0
            else "Found code cleanup issues",
            details={'issues': issues}
        )

    def _check_validation_mixing(self, path: Path) -> bool:
        """Check validation_mixing.py syntax."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for basic syntax
            ast.parse(content)

            # Check for class definitions with parentheses
            class_pattern = r'class\s+\w+\s*:'
            improper_classes = re.findall(class_pattern, content)

            return len(improper_classes) == 0

        except Exception:
            return False

    def _check_pyproject_toml(self, path: Path) -> bool:
        """Check pyproject.toml.py syntax."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Check for basic syntax
            ast.parse(content)

            # No single equals signs allowed
            assignment_pattern = r'(?<![\=\!<>])\s*=\s*(?!=)'
            improper_assignments = re.findall(assignment_pattern, content)

            return len(improper_assignments) == 0

        except Exception:
            return False

    def _generate_report(self) -> None:
        """Generate a detailed verification report."""
        report_path = self.project_root / "verification_report.md"

        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("# Fix Verification Report\n\n")

            for check_name, result in self.results.items():
                f.write(f"## {check_name.replace('_', ' ').title()}\n\n")
                status = '✓ PASSED' if result.passed else '✗ FAILED'
                f.write(f"Status: {status}\n\n")
                f.write(f"Message: {result.message}\n\n")

                if result.details:
                    f.write("Details:\n\n")
                    for key, value in result.details.items():
                        if isinstance(value, list):
                            f.write(f"* {key}:\n")
                            for item in value:
                                f.write(f"  - {item}\n")
                        else:
                            f.write(f"* {key}: {value}\n")
                    f.write("\n")

            self.logger.info(f"Verification report generated at {report_path}")


def main() -> None:
    """Main entry point for the verification script."""
    try:
        # Get project root
        if len(sys.argv) > 1:
            project_root = Path(sys.argv[1])
        else:
            project_root = Path(__file__).resolve().parent.parent

        # Run verification
        verifier = FixVerifier(project_root)
        success = verifier.verify_all()

        # Exit with appropriate status
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"Verification failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()