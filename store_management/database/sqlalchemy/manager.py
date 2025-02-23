"""
Database manager using SQLAlchemy ORM for the store management system.
"""
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import List, Optional, Dict, Any, Type, Union
from datetime import datetime

from database.sqlalchemy.models_file import Base
import database.sqlalchemy.models_file as models

class DatabaseError(Exception):
    """Custom database error for SQLAlchemy operations"""
    pass

class BaseManager:
    """Base manager class with common session and logging methods"""
    def __init__(self, session_factory):
        """
        Initialize base manager with session factory

        Args:
            session_factory: SQLAlchemy session factory
        """
        self.session_factory = session_factory
        self.logger = None  # Placeholder for logging

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations

        Yields:
            SQLAlchemy Session
        """
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.close()

class DatabaseManagerSQLAlchemy:
    """Comprehensive database manager using SQLAlchemy ORM"""

    def __init__(self, database_url: str):
        """
        Initialize database manager with database URL

        Args:
            database_url (str): SQLAlchemy database connection URL
        """
        try:
            # Create engine and session factory
            self.engine = create_engine(database_url)
            self.SessionFactory = sessionmaker(bind=self.engine)
            self._session: Optional[Session] = None
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {str(e)}")

    @property
    def session(self) -> Session:
        """
        Get current session or create a new one

        Returns:
            SQLAlchemy Session
        """
        if self._session is None:
            self._session = self.SessionFactory()
        return self._session

    @contextmanager
    def session_scope(self):
        """
        Provide a transactional scope around a series of operations

        Yields:
            SQLAlchemy Session
        """
        session = self.SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"Transaction failed: {str(e)}")
        finally:
            session.close()

    def get_model_columns(self, model: Type[models.Base]) -> List[str]:
        """
        Get column names for a specific model

        Args:
            model (Type[models.Base]): SQLAlchemy model class

        Returns:
            List of column names
        """
        return [column.key for column in inspect(model).columns]

    def add_record(self, model: Type[models.Base], data: Dict[str, Any]) -> Optional[models.Base]:
        """
        Add a new record to the database

        Args:
            model (Type[models.Base]): Model class
            data (Dict[str, Any]): Record data

        Returns:
            Newly created record or None
        """
        try:
            with self.session_scope() as session:
                record = model(**data)
                session.add(record)
                session.commit()
                session.refresh(record)
                return record
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to add record: {str(e)}")

    def update_record(self, model: Type[Base], record_id: int, data: Dict[str, Any]) -> Optional[Base]:
        """
        Update an existing record

        Args:
            model (Type[Base]): Model class
            record_id (int): Record ID
            data (Dict[str, Any]): Updated data

        Returns:
            Updated record or None
        """
        try:
            with self.session_scope() as session:
                record = session.query(model).get(record_id)
                if record:
                    for key, value in data.items():
                        setattr(record, key, value)
                    record.modified_at = datetime.utcnow()
                    session.commit()
                    session.refresh(record)
                    return record
                return None
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to update record: {str(e)}")

    def delete_record(self, model: Type[Base], record_id: int) -> bool:
        """
        Delete a record from the database

        Args:
            model (Type[Base]): Model class
            record_id (int): Record ID

        Returns:
            Boolean indicating success
        """
        try:
            with self.session_scope() as session:
                record = session.query(model).get(record_id)
                if record:
                    session.delete(record)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to delete record: {str(e)}")

    def get_record(self, model: Type[Base], record_id: int) -> Optional[Base]:
        """
        Get a single record by ID

        Args:
            model (Type[Base]): Model class
            record_id (int): Record ID

        Returns:
            Record or None
        """
        try:
            with self.session_scope() as session:
                return session.query(model).get(record_id)
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get record: {str(e)}")

    def get_all_records(self, model: Type[Base], **filters) -> List[Base]:
        """
        Get all records of a model, optionally filtered

        Args:
            model (Type[Base]): Model class
            **filters: Optional filter conditions

        Returns:
            List of records
        """
        try:
            with self.session_scope() as session:
                query = session.query(model)
                if filters:
                    query = query.filter_by(**filters)
                return query.all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to get records: {str(e)}")

    def search_records(self, model: Type[Base], search_term: str, *fields) -> List[Base]:
        """
        Search for records across specified fields

        Args:
            model (Type[Base]): Model class
            search_term (str): Term to search for
            *fields: Fields to search in

        Returns:
            List of matching records
        """
        try:
            with self.session_scope() as session:
                query = session.query(model)
                conditions = []
                for field in fields:
                    conditions.append(getattr(model, field).ilike(f"%{search_term}%"))
                return query.filter(or_(*conditions)).all()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to search records: {str(e)}")

    def bulk_update(self, model: Type[Base], updates: List[Dict[str, Any]]) -> bool:
        """
        Perform bulk updates on records

        Args:
            model (Type[Base]): Model class
            updates (List[Dict]): List of update dictionaries

        Returns:
            Boolean indicating success
        """
        try:
            with self.session_scope() as session:
                for update in updates:
                    record_id = update.pop('id', None)
                    if record_id:
                        record = session.query(model).get(record_id)
                        if record:
                            for key, value in update.items():
                                setattr(record, key, value)
                            record.modified_at = datetime.utcnow()
                session.commit()
                return True
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to perform bulk update: {str(e)}")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Any]:
        """
        Execute a raw SQL query

        Args:
            query (str): SQL query string
            params (Optional[tuple]): Query parameters

        Returns:
            List of query results
        """
        try:
            with self.session_scope() as session:
                result = session.execute(query, params or {})
                return result.fetchall()
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to execute query: {str(e)}")