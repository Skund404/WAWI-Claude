from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy_utils import database_exists, create_database
from store_management.database.sqlalchemy.models import Base
import os
from typing import List, Dict, Optional
from .manager import DatabaseManagerSQLAlchemy
from .models import Shelf


# Determine database path (use an environment variable or default)
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///./store_management.db'
)


class ShelfManager:
    """
    Specialized manager for Shelf-related operations
    """

    def __init__(self, session_factory):
        """
        Initialize ShelfManager with a session factory

        Args:
            session_factory: Function to create database sessions
        """
        self.session_factory = session_factory

    def get_all_shelves(self) -> List[Shelf]:
        """
        Retrieve all shelf items

        Returns:
            List[Shelf]: List of all shelf items
        """
        with self.session_factory() as session:
            return session.query(Shelf).all()

    def add_shelf_item(self, data: Dict) -> Optional[Shelf]:
        """
        Add a new shelf item to the database

        Args:
            data (Dict): Shelf item data

        Returns:
            Optional[Shelf]: Added shelf item or None
        """
        try:
            with self.session_factory() as session:
                # Prepare shelf item data
                shelf_data = {
                    'unique_id_leather': data.get('unique_id_leather'),
                    'name': data.get('name'),
                    'shelf_location': data.get('shelf'),
                    'shelf_type': data.get('type')
                }

                # Clean out None values
                shelf_data = {k: v for k, v in shelf_data.items() if v is not None}

                # Create new Shelf object
                new_shelf = Shelf(**shelf_data)
                session.add(new_shelf)
                session.commit()
                session.refresh(new_shelf)
                return new_shelf
        except Exception as e:
            print(f"Failed to add shelf item: {e}")
            return None

    def update_shelf_item(self, unique_id: str, update_data: Dict) -> bool:
        """
        Update a shelf item

        Args:
            unique_id (str): Unique identifier of the shelf item
            update_data (Dict): Data to update

        Returns:
            bool: True if update successful, False otherwise
        """
        try:
            with self.session_factory() as session:
                item = session.query(Shelf).filter_by(unique_id_leather=unique_id).first()
                if item:
                    for key, value in update_data.items():
                        if hasattr(item, key):
                            setattr(item, key, value)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Failed to update shelf item: {e}")
            return False

    def delete_shelf_item(self, unique_id: str) -> bool:
        """
        Delete a shelf item

        Args:
            unique_id (str): Unique identifier of the shelf item

        Returns:
            bool: True if deletion successful, False otherwise
        """
        try:
            with self.session_factory() as session:
                item = session.query(Shelf).filter_by(unique_id_leather=unique_id).first()
                if item:
                    session.delete(item)
                    session.commit()
                    return True
                return False
        except Exception as e:
            print(f"Failed to delete shelf item: {e}")
            return False

    def check_shelf_location_exists(self, shelf_location: str) -> bool:
        """
        Check if a shelf location is already in use

        Args:
            shelf_location (str): Shelf location to check

        Returns:
            bool: True if shelf location exists, False otherwise
        """
        try:
            with self.session_factory() as session:
                return session.query(Shelf).filter_by(shelf_location=shelf_location).first() is not None
        except Exception as e:
            print(f"Failed to check shelf location: {e}")
            return False

    def filter_shelves(self, filters: List[Dict]) -> List[Shelf]:
        """
        Filter shelf items based on multiple criteria

        Args:
            filters (List[Dict]): List of filter conditions

        Returns:
            List[Shelf]: Filtered shelf items
        """
        try:
            with self.session_factory() as session:
                query = session.query(Shelf)

                for filter_condition in filters:
                    column = filter_condition.get('column')
                    operator = filter_condition.get('operator')
                    value = filter_condition.get('value')

                    if column and operator and value is not None:
                        # Dynamic filtering based on column and operator
                        if operator == '=':
                            query = query.filter(getattr(Shelf, column) == value)
                        elif operator == 'like':
                            query = query.filter(getattr(Shelf, column).like(f"%{value}%"))
                        elif operator == '>':
                            query = query.filter(getattr(Shelf, column) > value)
                        elif operator == '<':
                            query = query.filter(getattr(Shelf, column) < value)

                return query.all()
        except Exception as e:
            print(f"Failed to filter shelves: {e}")
            return []

def init_database():
    """Initialize database if not exists"""
    if not database_exists(DATABASE_URL):
        create_database(DATABASE_URL)
        print("Database created successfully.")

    # Create all tables
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

def get_session():
    """Create and return a new database session"""
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()