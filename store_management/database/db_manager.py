# database/db_manager.py
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from utils.logger import logger, log_error
from utils.error_handler import DatabaseError


class DatabaseManager:
    def print_table_info(self, table_name):
        self.connect()
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            print(f"Table structure for {table_name}:")
            for column in columns:
                print(f"- {column[1]} ({column[2]})")
        finally:
            self.disconnect()

    def is_connected(self):
        return self.conn is not None and self.cursor is not None
    def print_all_table_columns(self):
        """Print columns for all tables in the database"""
        try:
            # Get list of all tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = self.cursor.fetchall()

            for table in tables:
                table_name = table[0]
                print(f"\nColumns for table: {table_name}")
                self.cursor.execute(f"PRAGMA table_info({table_name});")
                columns = self.cursor.fetchall()
                for column in columns:
                    print(f"- {column[1]} (Type: {column[2]})")
        except sqlite3.Error as e:
            print(f"Error retrieving table columns: {e}")

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        logger.debug(f"DatabaseManager initialized with path: {db_path}")

    def connect(self) -> bool:
        """Establish database connection with error handling"""
        if self.is_connected():
            return True
        try:
            logger.debug(f"Attempting to connect to database: {self.db_path}")
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info("Database connection established successfully")
            return True
        except sqlite3.Error as e:
            error_msg = f"Failed to connect to database: {self.db_path}"
            log_error(e, error_msg)
            self.conn = None
            self.cursor = None
            raise DatabaseError(error_msg, str(e))

    def disconnect(self):
        """Close database connection with error handling"""
        try:
            if self.conn:
                if self.conn.in_transaction:
                    self.conn.commit()
                self.conn.close()
                self.conn = None
                self.cursor = None
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
        """Delete a record with enhanced error handling and logging"""
        if not self.is_connected():
            self.connect()
        try:
            logger.debug(f"Attempting to delete record from {table}")
            logger.debug(f"Condition: {condition}")
            logger.debug(f"Condition params: {condition_params}")

            # Verify table exists
            if not self.table_exists(table):
                raise DatabaseError(f"Table does not exist: {table}")

            # First, check how many records would be deleted
            count_query = f"SELECT COUNT(*) FROM {table} WHERE {condition}"
            self.cursor.execute(count_query, condition_params)
            records_to_delete = self.cursor.fetchone()[0]
            logger.info(f"Number of records to be deleted: {records_to_delete}")

            # If no records to delete, log and return
            if records_to_delete == 0:
                logger.warning(f"No records found to delete from {table} with given condition")
                return False

            # Perform the actual deletion
            query = f"DELETE FROM {table} WHERE {condition}"
            self.cursor.execute(query, condition_params)
            self.conn.commit()

            # Verify deletion
            self.cursor.execute(count_query, condition_params)
            remaining_records = self.cursor.fetchone()[0]
            logger.info(f"Remaining records after deletion: {remaining_records}")

            rows_affected = self.cursor.rowcount
            logger.info(f"Successfully deleted {rows_affected} records from {table}")

            return rows_affected > 0

        except sqlite3.Error as e:
            # More detailed error logging
            error_msg = f"Detailed delete error in {table}: {str(e)}"
            logger.error(error_msg)

            # Log the full query and parameters for debugging
            logger.error(f"Delete query: {query}")
            logger.error(f"Parameters: {condition_params}")

            # Rollback the transaction
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