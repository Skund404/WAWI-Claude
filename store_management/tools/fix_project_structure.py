from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
A comprehensive script to verify and fix project structure issues.
This script:
1. Verifies all structural requirements
2. Automatically fixes identified issues
3. Opens the report after completion

Author: Project Optimization Team
Date: 2024-02-24
"""


class LogManager:
    """Manages log file handling and centralization."""

        @inject(MaterialService)
        def __init__(self, project_root: Path):
        self.project_root = project_root
        self.logs_dir = project_root / 'logs'
        self.logs_dir.mkdir(exist_ok=True)
        self.temp_log = project_root / 'temp_verification.log'
        self.file_handler = logging.FileHandler(self.temp_log)
        self.console_handler = logging.StreamHandler(sys.stdout)
        logging.basicConfig(level=logging.INFO, format=
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[self.file_handler, self.console_handler])
        self.logger = logging.getLogger(__name__)

        @inject(MaterialService)
        def cleanup_and_centralize(self) ->None:
        """Cleanup logging and move logs to centralized location."""
        self.file_handler.close()
        logging.getLogger().removeHandler(self.file_handler)
        log_files = [('temp_verification.log', 'tool_verification.log'), (
            'fix_verification.log', 'tool_fix_verification.log'), (
            'project_fixes.log', 'tool_project_fixes.log')]
        for src_name, dst_name in log_files:
            src = self.project_root / src_name
            if src.exists():
                try:
                    dst = self.logs_dir / dst_name
                    shutil.move(str(src), str(dst))
                    print(f'Moved {src_name} to logs directory')
                except Exception as e:
                    print(f'Error moving {src_name}: {e}')


@dataclass
class VerificationResult:
    """Results of a verification check."""
    passed: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    fix_function: Optional[callable] = None


class ProjectFixer:
    """Handles both verification and fixing of project issues."""

        @inject(MaterialService)
        def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.results: Dict[str, VerificationResult] = {}
        self.logs_dir = self.project_root / 'logs'
        self.backups_dir = self.project_root / 'backups'
        self.logs_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)
        self.log_manager = LogManager(project_root)
        self.logger = logging.getLogger(__name__)
        self.backup_path: Optional[Path] = None

        @inject(MaterialService)
        def verify_and_fix(self) ->bool:
        """Run all verifications and fix any issues found."""
        self.logger.info('Starting project verification and fixes...')
        try:
            self._create_backup()
            self._run_verifications()
            self._fix_issues()
            self._run_verifications()
            self._generate_report()
            self._open_report()
            self.log_manager.cleanup_and_centralize()
            all_passed = all(result.passed for result in self.results.values())
            status = 'completed successfully' if all_passed else 'found issues'
            print(f'Project fixes {status}')
            return all_passed
        except Exception as e:
            self.logger.error(f'Error during fix process: {e}')
            self._restore_backup()
            return False

        @inject(MaterialService)
        def _create_backup(self) ->None:
        """Create a backup of the project."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.backup_path = (self.project_root.parent /
            f'{self.project_root.name}_backup_{timestamp}')
        shutil.copytree(self.project_root, self.backup_path)
        self.logger.info(f'Created backup at {self.backup_path}')

        @inject(MaterialService)
        def _restore_backup(self) ->None:
        """Restore from backup if available."""
        if self.backup_path and self.backup_path.exists():
            shutil.rmtree(self.project_root)
            shutil.copytree(self.backup_path, self.project_root)
            self.logger.info('Restored from backup')

        @inject(MaterialService)
        def _run_verifications(self) ->None:
        """Run all verifications."""
        verifications = [('log_centralization', self._verify_logs, self.
            _fix_logs), ('backup_consolidation', self._verify_backups, self
            ._fix_backups), ('service_consolidation', self._verify_services,
            self._fix_services), ('config_standardization', self.
            _verify_config, self._fix_config), ('code_cleanup', self.
            _verify_code, self._fix_code)]
        for name, verify_func, fix_func in verifications:
            result = verify_func()
            result.fix_function = fix_func
            self.results[name] = result

        @inject(MaterialService)
        def _fix_issues(self) ->None:
        """Fix any issues found during verification."""
        for name, result in self.results.items():
            if not result.passed and result.fix_function:
                self.logger.info(f'Fixing {name}...')
                try:
                    result.fix_function()
                except Exception as e:
                    self.logger.error(f'Error fixing {name}: {e}')

        @inject(MaterialService)
        def _verify_logs(self) ->VerificationResult:
        """Verify log centralization."""
        scattered_logs = []
        for log_file in self.project_root.rglob('*.log'):
            if log_file.name == 'temp_verification.log':
                continue
            if 'logs' not in str(log_file.parent).split(os.sep):
                scattered_logs.append(str(log_file))
        return VerificationResult(passed=len(scattered_logs) == 0, message=
            'All logs are centralized' if len(scattered_logs) == 0 else
            'Found scattered log files', details={'scattered_logs':
            scattered_logs})

        @inject(MaterialService)
        def _fix_logs(self) ->None:
        """Fix log centralization issues."""
        for log_file in self.project_root.rglob('*.log'):
            if 'logs' not in str(log_file.parent).split(os.sep):
                try:
                    new_path = (self.logs_dir /
                        f'{log_file.parent.name}_{log_file.name}')
                    shutil.move(str(log_file), str(new_path))
                except Exception as e:
                    self.logger.error(f'Error moving log file {log_file}: {e}')

        @inject(MaterialService)
        def _verify_code(self) ->VerificationResult:
        """Verify code cleanup."""
        issues = []
        mixing_path = (self.project_root /
            'database/sqlalchemy/mixins/validation_mixing.py')
        if mixing_path.exists():
            with open(mixing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if re.search('class\\s+\\w+\\s*:', content):
                issues.append(
                    'Syntax check failed for database/sqlalchemy/mixins/validation_mixing.py'
                    )
        return VerificationResult(passed=len(issues) == 0, message=
            'Code cleanup is complete' if len(issues) == 0 else
            'Found code cleanup issues', details={'issues': issues})

        @inject(MaterialService)
        def _fix_code(self) ->None:
        """Fix code issues."""
        mixing_path = (self.project_root /
            'database/sqlalchemy/mixins/validation_mixing.py')
        if mixing_path.exists():
            with open(mixing_path, 'r', encoding='utf-8') as f:
                content = f.read()
            fixed_content = re.sub('class\\s+(\\w+)\\s*:',
                'class \\1(object):', content)
            with open(mixing_path, 'w', encoding='utf-8') as f:
                f.write(fixed_content)

        @inject(MaterialService)
        def _verify_backups(self) ->VerificationResult:
        """Verify backup consolidation."""
        scattered_backups = []
        for pattern in ['*.bak', '*.backup', '*_backup_*']:
            for backup_file in self.project_root.rglob(pattern):
                if 'backups' not in str(backup_file.parent).split(os.sep):
                    scattered_backups.append(str(backup_file))
        return VerificationResult(passed=len(scattered_backups) == 0,
            message='All backups are consolidated' if len(scattered_backups
            ) == 0 else 'Found scattered backup files', details={
            'scattered_backups': scattered_backups})

        @inject(MaterialService)
        def _fix_backups(self) ->None:
        """Fix backup consolidation issues."""
        for pattern in ['*.bak', '*.backup', '*_backup_*']:
            for backup_file in self.project_root.rglob(pattern):
                if 'backups' not in str(backup_file.parent).split(os.sep):
                    try:
                        new_path = (self.backups_dir /
                            f'{backup_file.parent.name}_{backup_file.name}')
                        shutil.move(str(backup_file), str(new_path))
                    except Exception as e:
                        self.logger.error(
                            f'Error moving backup file {backup_file}: {e}')

        @inject(MaterialService)
        def _verify_services(self) ->VerificationResult:
        """Verify service consolidation."""
        services_dir = self.project_root / 'services'
        implementations_dir = services_dir / 'implementations'
        issues = []
        if services_dir.exists():
            for service_file in services_dir.glob('*_service.py'):
                if service_file.parent == services_dir:
                    issues.append(
                        f'Service file outside implementations: {service_file}'
                        )
        return VerificationResult(passed=len(issues) == 0, message=
            'Services are properly consolidated' if len(issues) == 0 else
            'Found service consolidation issues', details={'issues': issues})

        @inject(MaterialService)
        def _fix_services(self) ->None:
        """Fix service consolidation issues."""
        services_dir = self.project_root / 'services'
        implementations_dir = services_dir / 'implementations'
        implementations_dir.mkdir(exist_ok=True)
        for service_file in services_dir.glob('*_service.py'):
            if service_file.parent == services_dir:
                try:
                    new_path = implementations_dir / service_file.name
                    shutil.move(str(service_file), str(new_path))
                except Exception as e:
                    self.logger.error(
                        f'Error moving service file {service_file}: {e}')

        @inject(MaterialService)
        def _verify_config(self) ->VerificationResult:
        """Verify configuration standardization."""
        config_dir = self.project_root / 'config'
        central_config = config_dir / 'configuration.py'
        issues = []
        if not central_config.exists():
            issues.append('Missing centralized configuration file')
        return VerificationResult(passed=len(issues) == 0, message=
            'Configuration is properly standardized' if len(issues) == 0 else
            'Found configuration issues', details={'issues': issues})

        @inject(MaterialService)
        def _fix_config(self) ->None:
        """Fix configuration issues."""
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        central_config = config_dir / 'configuration.py'
        if not central_config.exists():
            config_template = """""\"
Centralized configuration for the project.
""\"

class Configuration:
    ""\"Central configuration management.""\"

    # Add configuration values here
    DEBUG = False
    LOG_LEVEL = "INFO"
    DATABASE_PATH = "data/store.db\"
"""
            with open(central_config, 'w', encoding='utf-8') as f:
                f.write(config_template)

        @inject(MaterialService)
        def _generate_report(self) ->None:
        """Generate verification and fix report."""
        report_path = self.project_root / 'verification_report.md'
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('# Fix Verification Report\n\n')
            for check_name, result in self.results.items():
                f.write(f"## {check_name.replace('_', ' ').title()}\n\n")
                status = '✓ PASSED' if result.passed else '✗ FAILED'
                f.write(f'Status: {status}\n\n')
                f.write(f'Message: {result.message}\n\n')
                if result.details:
                    f.write('Details:\n\n')
                    for key, value in result.details.items():
                        if isinstance(value, list):
                            f.write(f'* {key}:\n')
                            for item in value:
                                f.write(f'  - {item}\n')
                        else:
                            f.write(f'* {key}: {value}\n')
                    f.write('\n')
        self.logger.info(f'Generated report at {report_path}')

        @inject(MaterialService)
        def _open_report(self) ->None:
        """Open the verification report."""
        report_path = self.project_root / 'verification_report.md'
        try:
            if sys.platform == 'win32':
                os.startfile(report_path)
            elif sys.platform == 'darwin':
                subprocess.run(['open', report_path])
            else:
                subprocess.run(['xdg-open', report_path])
        except Exception as e:
            self.logger.error(f'Error opening report: {e}')


def main() ->None:
    """Main entry point for the script."""
    try:
        if len(sys.argv) > 1:
            project_root = Path(sys.argv[1])
        else:
            project_root = Path(__file__).resolve().parent.parent
        fixer = ProjectFixer(project_root)
        success = fixer.verify_and_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f'Project fixes failed: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
