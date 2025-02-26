def get_database_path() -> str:
    root_dir = _find_project_root()
    db_dir = root_dir / 'data'

    # Ensure the data directory exists with full permissions
    os.makedirs(db_dir, mode=0o777, exist_ok=True)

    # Log additional path information
    logger.info(f"Database directory: {db_dir}")
    logger.info(f"Database directory absolute path: {db_dir.absolute()}")
    logger.info(f"Database directory permissions: {oct(db_dir.stat().st_mode)}")

    return str(db_dir / 'store_management.db')