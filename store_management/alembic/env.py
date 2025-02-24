from di.core import inject
from services.interfaces import MaterialService, ProjectService, InventoryService, OrderService
project_root = Path(__file__).resolve().parent.parent
print(f'Project root: {project_root}')
sys.path.insert(0, str(project_root))
print(f'Python executable: {sys.executable}')
print(f'sys.path: {sys.path}')
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_offline() ->None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option('sqlalchemy.url')
    context.configure(url=url, target_metadata=target_metadata,
        literal_binds=True, dialect_opts={'paramstyle': 'named'},
        version_table='alembic_version')
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() ->None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(config.get_main_option('sqlalchemy.url'))
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=
            target_metadata, version_table='alembic_version')
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
