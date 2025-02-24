from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
"""
F:/WAWI Homebrew/WAWI Claude/store_management/database/version_manager.py

Database version management for tracking schema versions.
"""
logger = logging.getLogger(__name__)


class DatabaseVersionManager:
    """
    Database version manager for tracking schema versions.

    This class provides methods for tracking database schema versions
    and ensuring compatibility between the application and the database.
    """

        @inject(MaterialService)
        def __init__(self, database_url: Optional[str]=None):
        """
        Initialize a new DatabaseVersionManager.

        Args:
            database_url: The database URL. If not provided, the default from DatabaseConfig is used.
        """
        self.database_url = database_url or DatabaseConfig.get_database_url()
        self.engine = create_engine(self.database_url)
        self.metadata = MetaData()
        self.schema_versions = Table('schema_versions', self.metadata,
            Column('id', Integer, primary_key=True), Column('version',
            String(50), nullable=False), Column('applied_at', DateTime,
            default=datetime.datetime.utcnow), Column('description', Text),
            Column('applied_by', String(100)), Column('script_name', String
            (255)))
        self.schema_migrations = Table('schema_migrations', self.metadata,
            Column('id', Integer, primary_key=True), Column('migration_id',
            String(50), nullable=False, unique=True), Column('applied_at',
            DateTime, default=datetime.datetime.utcnow), Column(
            'description', Text), Column('applied_by', String(100)), Column
            ('script_name', String(255)))

        @inject(MaterialService)
        def initialize(self) ->None:
        """
        Initialize the version tracking tables.

        This method creates the tables needed for tracking schema versions.
        """
        try:
            self.metadata.create_all(self.engine)
            logger.info('Version tracking tables initialized successfully')
            with self.engine.connect() as connection:
                result = connection.execute(select(self.schema_versions))
                if result.first() is None:
                    connection.execute(insert(self.schema_versions).values(
                        version='1.0.0', description=
                        'Initial schema version', applied_by='system',
                        script_name='version_manager.py'))
                    connection.commit()
                    logger.info('Added initial schema version record')
        except Exception as e:
            logger.error(
                f'Failed to initialize version tracking tables: {str(e)}')
            raise

        @inject(MaterialService)
        def get_current_version(self) ->str:
        """
        Get the current database schema version.

        Returns:
            Current schema version.
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(select(self.schema_versions).
                    order_by(self.schema_versions.c.id.desc()))
                record = result.first()
                if record is None:
                    return 'Unknown'
                return record.version
        except Exception as e:
            logger.error(f'Failed to get current schema version: {str(e)}')
            return 'Error'

        @inject(MaterialService)
        def update_version(self, version: str, description: str, applied_by:
        str='system', script_name: str=None) ->None:
        """
        Update the database schema version.

        Args:
            version: The new schema version.
            description: Description of the version changes.
            applied_by: Name of the user or process that applied the update.
            script_name: Name of the script that applied the update.
        """
        try:
            with self.engine.connect() as connection:
                connection.execute(insert(self.schema_versions).values(
                    version=version, description=description, applied_by=
                    applied_by, script_name=script_name or
                    'version_manager.py'))
                connection.commit()
                logger.info(f'Updated schema version to {version}')
        except Exception as e:
            logger.error(f'Failed to update schema version: {str(e)}')
            raise

        @inject(MaterialService)
        def get_version_history(self) ->List[Dict[str, Any]]:
        """
        Get the database schema version history.

        Returns:
            List of dictionaries with version history information.
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(select(self.schema_versions).
                    order_by(self.schema_versions.c.id.desc()))
                history = []
                for record in result:
                    history.append({'id': record.id, 'version': record.
                        version, 'applied_at': record.applied_at,
                        'description': record.description, 'applied_by':
                        record.applied_by, 'script_name': record.script_name})
                return history
        except Exception as e:
            logger.error(f'Failed to get version history: {str(e)}')
            return []

        @inject(MaterialService)
        def record_migration(self, migration_id: str, description: str,
        applied_by: str='system', script_name: str=None) ->None:
        """
        Record a database migration.

        Args:
            migration_id: The migration ID.
            description: Description of the migration.
            applied_by: Name of the user or process that applied the migration.
            script_name: Name of the script that applied the migration.
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(select(self.schema_migrations).
                    where(self.schema_migrations.c.migration_id ==
                    migration_id))
                if result.first() is None:
                    connection.execute(insert(self.schema_migrations).
                        values(migration_id=migration_id, description=
                        description, applied_by=applied_by, script_name=
                        script_name or 'version_manager.py'))
                    connection.commit()
                    logger.info(f'Recorded migration: {migration_id}')
                else:
                    logger.info(
                        f'Migration {migration_id} already recorded, skipping')
        except Exception as e:
            logger.error(f'Failed to record migration: {str(e)}')
            raise

        @inject(MaterialService)
        def get_applied_migrations(self) ->List[str]:
        """
        Get the list of applied migration IDs.

        Returns:
            List of applied migration IDs.
        """
        try:
            with self.engine.connect() as connection:
                result = connection.execute(select(self.schema_migrations.c
                    .migration_id))
                return [row.migration_id for row in result]
        except Exception as e:
            logger.error(f'Failed to get applied migrations: {str(e)}')
            return []

        @inject(MaterialService)
        def check_compatibility(self, required_version: str) ->bool:
        """
        Check if the database schema is compatible with the application.

        Args:
            required_version: The version required by the application.

        Returns:
            True if the database schema is compatible, False otherwise.
        """
        current_version = self.get_current_version()
        try:
            current_parts = [int(p) for p in current_version.split('.')]
            required_parts = [int(p) for p in required_version.split('.')]
            if current_parts[0] != required_parts[0]:
                logger.warning(
                    f'Major version mismatch: DB={current_version}, App={required_version}'
                    )
                return False
            for i in range(min(len(current_parts), len(required_parts))):
                if current_parts[i] < required_parts[i]:
                    logger.warning(
                        f'DB version {current_version} is older than required version {required_version}'
                        )
                    return False
                elif current_parts[i] > required_parts[i]:
                    break
            return True
        except (ValueError, IndexError):
            logger.error(
                f'Failed to compare versions: DB={current_version}, App={required_version}'
                )
            return False


version_manager = DatabaseVersionManager()
