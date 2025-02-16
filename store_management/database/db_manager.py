# database/db_manager.py
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path
import json


class DatabaseManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except sqlite3.Error as e:
            print(f"Error connecting to database: {e}")
            return False

    def disconnect(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def execute_query(self, query: str, params: tuple = None) -> Optional[List[tuple]]:
        """Execute a SQL query and return results"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error executing query: {e}")
            return None

    def insert_record(self, table: str, data: Dict[str, Any]) -> bool:
        """Insert a new record into the specified table"""
        try:
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

            self.cursor.execute(query, tuple(data.values()))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error inserting record: {e}")
            self.conn.rollback()
            return False

    def update_record(self, table: str, data: Dict[str, Any], condition: str,
                      condition_params: tuple) -> bool:
        """Update an existing record in the specified table"""
        try:
            set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
            query = f"UPDATE {table} SET {set_clause} WHERE {condition}"

            params = tuple(data.values()) + condition_params
            self.cursor.execute(query, params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error updating record: {e}")
            self.conn.rollback()
            return False

    def delete_record(self, table: str, condition: str, condition_params: tuple) -> bool:
        """Delete a record from the specified table"""
        try:
            query = f"DELETE FROM {table} WHERE {condition}"
            self.cursor.execute(query, condition_params)
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error deleting record: {e}")
            self.conn.rollback()
            return False

    def log_action(self, table: str, action: str, record_id: str,
                   old_values: Optional[Dict] = None,
                   new_values: Optional[Dict] = None) -> bool:
        """Log an action in the audit_log table"""
        try:
            query = """
                INSERT INTO audit_log 
                (table_name, action, record_id, old_values, new_values)
                VALUES (?, ?, ?, ?, ?)
            """
            old_values_json = json.dumps(old_values) if old_values else None
            new_values_json = json.dumps(new_values) if new_values else None

            self.cursor.execute(query, (table, action, record_id,
                                        old_values_json, new_values_json))
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Error logging action: {e}")
            return False

    def __enter__(self):
        """Context manager enter"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()