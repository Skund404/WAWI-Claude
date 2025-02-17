# database/db_manager.py
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from utils.logger import logger, log_error
from utils.error_handler import DatabaseError


class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        logger.debug(f"DatabaseManager initialized with path: {db_path}")

    def connect(self) -> bool:
        """Establish database connection with error handling"""
        try:
            logger.debug(f"Attempting to connect to database: {self.db_path}")

            # Close any existing connection
            if self.conn:
                self.disconnect()

            # Create new connection
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

            logger.info("Database connection established successfully")
            return True
        except sqlite3.Error as e:
            error_msg = f"Failed to connect to database: {self.db_path}"
            log_error(e, error_msg)
            # Reset connection objects
            self.conn = None
            self.cursor = None
            raise DatabaseError(error_msg, str(e))

    def disconnect(self):
        """Close database connection with error handling"""
        try:
            if self.conn:
                self.conn.close()
                logger.debug("Database connection closed")
        except sqlite3.Error as e:
            log_error(e, "Error closing database connection")

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[tuple]]:
        """Execute a SQL query with error handling"""
        try:
            logger.debug(f"Executing query: {query}")
            if params:
                logger.debug(f"Query parameters: {params}")
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)

            results = self.cursor.fetchall()
            logger.debug(f"Query returned {len(results)} results")
            return results

        except sqlite3.Error as e:
            error_msg = f"Error executing query: {query}"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def insert_record(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert a new record with error handling"""
        try:
            logger.debug(f"Inserting record into {table}")

            # Verify table exists
            if not self.table_exists(table):
                raise DatabaseError(f"Table does not exist: {table}")

            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            self.cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            logger.info(f"Successfully inserted record into {table}")
            return True

        except sqlite3.Error as e:
            error_msg = f"Failed to insert record into {table}"
            log_error(e, error_msg)
            self.conn.rollback()
            raise DatabaseError(error_msg, str(e))

    def update_record(self, table: str, data: Dict[str, Any], condition: str,
                      condition_params: tuple) -> bool:
        """Update an existing record with error handling"""
        try:
            logger.debug(f"Updating record in {table}")

            # Verify table exists
            if not self.table_exists(table):
                raise DatabaseError(f"Table does not exist: {table}")

            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"

            params = tuple(data.values()) + condition_params
            self.cursor.execute(query, params)
            self.conn.commit()

            rows_affected = self.cursor.rowcount
            logger.info(f"Successfully updated {rows_affected} records in {table}")
            return True

        except sqlite3.Error as e:
            error_msg = f"Failed to update record in {table}"
            log_error(e, error_msg)
            self.conn.rollback()
            raise DatabaseError(error_msg, str(e))

    def delete_record(self, table: str, condition: str, condition_params: tuple) -> bool:
        """Delete a record with error handling"""
        try:
            logger.debug(f"Deleting record from {table}")

            # Verify table exists
            if not self.table_exists(table):
                raise DatabaseError(f"Table does not exist: {table}")

            query = f"DELETE FROM {table} WHERE {condition}"
            self.cursor.execute(query, condition_params)
            self.conn.commit()

            rows_affected = self.cursor.rowcount
            logger.info(f"Successfully deleted {rows_affected} records from {table}")
            return True

        except sqlite3.Error as e:
            error_msg = f"Failed to delete record from {table}"
            log_error(e, error_msg)
            self.conn.rollback()
            raise DatabaseError(error_msg, str(e))

    def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database"""
        try:
            query = """
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """
            self.cursor.execute(query, (table_name,))
            return bool(self.cursor.fetchone())
        except sqlite3.Error as e:
            error_msg = f"Error checking table existence: {table_name}"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def get_table_info(self, table_name: str) -> List[tuple]:
        """Get information about table columns"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            error_msg = f"Error getting table info: {table_name}"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def verify_table_structure(self, table_name: str, required_columns: List[str]) -> bool:
        """Verify that a table has all required columns"""
        try:
            table_info = self.get_table_info(table_name)
            existing_columns = [col[1] for col in table_info]
            missing_columns = [col for col in required_columns if col not in existing_columns]

            if missing_columns:
                raise DatabaseError(
                    f"Table {table_name} is missing required columns: {missing_columns}"
                )
            return True

        except sqlite3.Error as e:
            error_msg = f"Error verifying table structure: {table_name}"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def get_table_columns(self, table_name: str) -> List[str]:
        """Get list of column names for a table"""
        try:
            table_info = self.get_table_info(table_name)
            return [col[1] for col in table_info]
        except sqlite3.Error as e:
            error_msg = f"Error getting table columns: {table_name}"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def __enter__(self):
        """Context manager enter"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

    def begin_transaction(self):
        """Begin a transaction"""
        try:
            self.conn.execute("BEGIN TRANSACTION")
            logger.debug("Transaction started")
        except sqlite3.Error as e:
            error_msg = "Failed to begin transaction"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def commit_transaction(self):
        """Commit a transaction"""
        try:
            self.conn.commit()
            logger.debug("Transaction committed")
        except sqlite3.Error as e:
            error_msg = "Failed to commit transaction"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))

    def rollback_transaction(self):
        """Rollback a transaction"""
        try:
            self.conn.rollback()
            logger.debug("Transaction rolled back")
        except sqlite3.Error as e:
            error_msg = "Failed to rollback transaction"
            log_error(e, error_msg)
            raise DatabaseError(error_msg, str(e))