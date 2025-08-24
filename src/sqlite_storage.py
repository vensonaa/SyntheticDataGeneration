"""
SQLite Storage Module for Synthetic Data Generation

This module provides functionality to store generated synthetic data in SQLite database
with automatic table creation, schema management, and data insertion.
"""

import os
import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteStorageManager:
    """Manages SQLite database operations for synthetic data storage"""
    
    def __init__(self, db_path: str = "synthetic_data.db"):
        """
        Initialize SQLite storage manager
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self._ensure_db_exists()
    
    def _ensure_db_exists(self):
        """Ensure database file exists and create if necessary"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        # Create connection to initialize database
        self.connection = sqlite3.connect(self.db_path)
        self.connection.close()
        logger.info(f"SQLite database initialized at: {self.db_path}")
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def create_table_from_schema(self, table_name: str, schema_definition: Dict[str, Any]) -> bool:
        """
        Create a table based on schema definition
        
        Args:
            table_name: Name of the table to create
            schema_definition: Schema definition dictionary
            
        Returns:
            True if table created successfully, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Sanitize table name for SQLite - remove invalid characters
            sanitized_table_name = table_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            sanitized_table_name = ''.join(c for c in sanitized_table_name if c.isalnum() or c == '_')
            
            # Extract fields from schema
            fields = schema_definition.get('fields', [])
            if not fields:
                logger.error(f"No fields found in schema for table {sanitized_table_name}")
                return False
            
            # Build CREATE TABLE statement
            field_definitions = []
            for field in fields:
                # Clean field name for SQLite - remove all invalid characters
                field_name = field.get('name', '').lower().replace(' ', '_').replace('-', '_').replace('.', '_')
                # Remove any other invalid characters
                field_name = ''.join(c for c in field_name if c.isalnum() or c == '_')
                
                data_type = self._map_data_type_to_sqlite(field.get('data_type', 'string'))
                constraints = []
                
                if field.get('required', True):
                    constraints.append('NOT NULL')
                
                if field.get('unique', False):
                    constraints.append('UNIQUE')
                
                field_def = f"{field_name} {data_type}"
                if constraints:
                    field_def += f" {' '.join(constraints)}"
                
                field_definitions.append(field_def)
            
            # Add metadata columns (only if not already present)
            existing_columns = [field.get('name', '').lower().replace(' ', '_') for field in fields]
            
            if 'id' not in existing_columns:
                field_definitions.append("id INTEGER PRIMARY KEY AUTOINCREMENT")
            
            field_definitions.extend([
                "created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "generation_metadata TEXT",
                "validation_status TEXT DEFAULT 'valid'"
            ])
            
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {sanitized_table_name} (
                {', '.join(field_definitions)}
            )
            """
            
            cursor.execute(create_table_sql)
            conn.commit()
            conn.close()
            
            logger.info(f"Table '{sanitized_table_name}' created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error creating table {sanitized_table_name}: {str(e)}")
            if conn:
                conn.close()
            return False
    
    def _map_data_type_to_sqlite(self, data_type: str) -> str:
        """
        Map data type to SQLite data type
        
        Args:
            data_type: Data type string
            
        Returns:
            SQLite data type
        """
        data_type_mapping = {
            'string': 'TEXT',
            'text': 'TEXT',
            'integer': 'INTEGER',
            'int': 'INTEGER',
            'float': 'REAL',
            'decimal': 'REAL',
            'boolean': 'INTEGER',  # SQLite doesn't have boolean, use INTEGER (0/1)
            'date': 'TEXT',  # Store as ISO format string
            'datetime': 'TEXT',  # Store as ISO format string
            'email': 'TEXT',
            'phone': 'TEXT',
            'name': 'TEXT',
            'address': 'TEXT',
            'url': 'TEXT',
            'uuid': 'TEXT'
        }
        
        return data_type_mapping.get(data_type.lower(), 'TEXT')
    
    def insert_data(self, table_name: str, data: List[Dict[str, Any]], 
                   schema_definition: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Insert data into SQLite table
        
        Args:
            table_name: Name of the table to insert data into
            data: List of data records to insert
            schema_definition: Optional schema definition for validation
            
        Returns:
            Dictionary with insertion results
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Sanitize table name for SQLite
            sanitized_table_name = table_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            sanitized_table_name = ''.join(c for c in sanitized_table_name if c.isalnum() or c == '_')
            
            if not data:
                return {
                    'success': True,
                    'inserted_count': 0,
                    'errors': [],
                    'message': 'No data to insert'
                }
            
            # Ensure table exists
            if not self._table_exists(sanitized_table_name):
                if schema_definition:
                    self.create_table_from_schema(table_name, schema_definition)
                else:
                    # Create table with inferred schema
                    self._create_table_from_data(sanitized_table_name, data)
            
            # Prepare data for insertion
            prepared_data = []
            errors = []
            
            for i, record in enumerate(data):
                try:
                    # Extract data from record structure
                    if isinstance(record, dict) and 'data' in record:
                        record_data = record['data']
                    else:
                        record_data = record
                    
                    # Prepare record for insertion
                    prepared_record = self._prepare_record_for_insertion(record_data, record)
                    prepared_data.append(prepared_record)
                    
                except Exception as e:
                    errors.append(f"Record {i}: {str(e)}")
                    logger.warning(f"Error preparing record {i}: {str(e)}")
            
            if not prepared_data:
                return {
                    'success': False,
                    'inserted_count': 0,
                    'errors': errors,
                    'message': 'No valid data to insert'
                }
            
            # Get column names from first record
            columns = list(prepared_data[0].keys())
            placeholders = ', '.join(['?' for _ in columns])
            
            # Debug logging
            logger.debug(f"Table: {sanitized_table_name}")
            logger.debug(f"Columns: {columns}")
            logger.debug(f"First record keys: {list(prepared_data[0].keys())}")
            
            # Build INSERT statement
            insert_sql = f"""
            INSERT INTO {sanitized_table_name} ({', '.join(columns)})
            VALUES ({placeholders})
            """
            
            logger.debug(f"INSERT SQL: {insert_sql}")
            
            # Insert data
            inserted_count = 0
            for record in prepared_data:
                try:
                    values = [record.get(col) for col in columns]
                    cursor.execute(insert_sql, values)
                    inserted_count += 1
                except Exception as e:
                    errors.append(f"Insert error: {str(e)}")
                    logger.warning(f"Error inserting record: {str(e)}")
            
            conn.commit()
            conn.close()
            
            return {
                'success': True,
                'inserted_count': inserted_count,
                'total_records': len(data),
                'errors': errors,
                'table_name': sanitized_table_name,
                'message': f'Successfully inserted {inserted_count} records into {sanitized_table_name}'
            }
            
        except Exception as e:
            logger.error(f"Error inserting data into {sanitized_table_name}: {str(e)}")
            if conn:
                conn.close()
            return {
                'success': False,
                'inserted_count': 0,
                'errors': [str(e)],
                'message': f'Failed to insert data: {str(e)}'
            }
    
    def _prepare_record_for_insertion(self, record_data: Dict[str, Any], 
                                    original_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a record for database insertion
        
        Args:
            record_data: The actual data dictionary
            original_record: The original record with metadata
            
        Returns:
            Prepared record for insertion
        """
        prepared_record = {}
        
        # Add data fields
        for key, value in record_data.items():
            # Clean column name - remove all invalid characters for SQLite
            clean_key = key.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            # Remove any other invalid characters
            clean_key = ''.join(c for c in clean_key if c.isalnum() or c == '_')
            
            # Debug logging
            logger.debug(f"Processing field: {key} -> {clean_key}, value: {value}, type: {type(value)}")
            
            # Handle different data types
            if isinstance(value, bool):
                prepared_record[clean_key] = 1 if value else 0
            elif isinstance(value, (dict, list)):
                prepared_record[clean_key] = json.dumps(value)
            elif value is None:
                # For NULL values, provide default values based on field type
                # This prevents NOT NULL constraint violations
                default_value = self._get_default_value_for_field(key)
                prepared_record[clean_key] = default_value
                logger.debug(f"Field {key} was NULL, using default: {default_value}")
            else:
                prepared_record[clean_key] = str(value)
        
        # Add metadata
        if 'generation_metadata' in original_record:
            prepared_record['generation_metadata'] = json.dumps(original_record['generation_metadata'])
        
        if 'validation_errors' in original_record and original_record['validation_errors']:
            prepared_record['validation_status'] = 'invalid'
        else:
            prepared_record['validation_status'] = 'valid'
        
        return prepared_record
    
    def _get_default_value_for_field(self, field_name: str) -> Any:
        """
        Get default value for a field based on its name or type
        
        Args:
            field_name: Name of the field
            
        Returns:
            Default value for the field
        """
        field_name_lower = field_name.lower()
        
        # Provide sensible defaults based on field name
        if any(keyword in field_name_lower for keyword in ['amount', 'price', 'cost', 'total', 'sum']):
            return 0.0
        elif any(keyword in field_name_lower for keyword in ['count', 'quantity', 'number', 'id']):
            return 0
        elif any(keyword in field_name_lower for keyword in ['name', 'title', 'description', 'text']):
            return ''
        elif any(keyword in field_name_lower for keyword in ['email', 'url', 'link']):
            return ''
        elif any(keyword in field_name_lower for keyword in ['date', 'time', 'created', 'updated']):
            return datetime.now().isoformat()
        elif any(keyword in field_name_lower for keyword in ['active', 'enabled', 'valid']):
            return 1  # True for boolean fields
        else:
            # Default to empty string for unknown field types
            return ''
    
    def _table_exists(self, table_name: str) -> bool:
        """Check if table exists"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name=?
            """, (table_name,))
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            logger.error(f"Error checking if table {table_name} exists: {str(e)}")
            return False
    
    def _create_table_from_data(self, table_name: str, data: List[Dict[str, Any]]) -> bool:
        """
        Create table with schema inferred from data
        
        Args:
            table_name: Name of the table to create
            data: Sample data to infer schema from
            
        Returns:
            True if table created successfully
        """
        try:
            if not data:
                return False
            
            # Get sample record
            sample_record = data[0]
            if isinstance(sample_record, dict) and 'data' in sample_record:
                sample_data = sample_record['data']
            else:
                sample_data = sample_record
            
            # Create schema definition from data
            fields = []
            for key, value in sample_data.items():
                field = {
                    'name': key,
                    'data_type': self._infer_data_type(value),
                    'required': False
                }
                fields.append(field)
            
            schema_definition = {
                'name': table_name,
                'fields': fields
            }
            
            return self.create_table_from_schema(table_name, schema_definition)
            
        except Exception as e:
            logger.error(f"Error creating table from data: {str(e)}")
            return False
    
    def _infer_data_type(self, value: Any) -> str:
        """Infer data type from value"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, str):
            # Try to infer more specific types
            if '@' in value and '.' in value:
                return 'email'
            elif value.replace('-', '').replace('(', '').replace(')', '').replace(' ', '').isdigit():
                return 'phone'
            else:
                return 'string'
        else:
            return 'string'
    
    def query_data(self, table_name: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Query data from table
        
        Args:
            table_name: Name of the table to query
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of records
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Sanitize table name
            sanitized_table_name = table_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            sanitized_table_name = ''.join(c for c in sanitized_table_name if c.isalnum() or c == '_')
            
            query = f"""
            SELECT * FROM {sanitized_table_name}
            ORDER BY id
            LIMIT ? OFFSET ?
            """
            
            cursor.execute(query, (limit, offset))
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = dict(zip(columns, row))
                records.append(record)
            
            conn.close()
            return records
            
        except Exception as e:
            logger.error(f"Error querying data from {table_name}: {str(e)}")
            if conn:
                conn.close()
            return []
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get information about a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Table information dictionary
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Sanitize table name
            sanitized_table_name = table_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            sanitized_table_name = ''.join(c for c in sanitized_table_name if c.isalnum() or c == '_')
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({sanitized_table_name})")
            columns = cursor.fetchall()
            
            # Get record count
            cursor.execute(f"SELECT COUNT(*) FROM {sanitized_table_name}")
            record_count = cursor.fetchone()[0]
            
            # Get sample data
            cursor.execute(f"SELECT * FROM {sanitized_table_name} LIMIT 5")
            sample_rows = cursor.fetchall()
            column_names = [description[0] for description in cursor.description]
            
            sample_data = []
            for row in sample_rows:
                sample_data.append(dict(zip(column_names, row)))
            
            conn.close()
            
            return {
                'table_name': sanitized_table_name,
                'columns': [{'name': col[1], 'type': col[2], 'not_null': col[3], 'primary_key': col[5]} for col in columns],
                'record_count': record_count,
                'sample_data': sample_data
            }
            
        except Exception as e:
            logger.error(f"Error getting table info for {sanitized_table_name}: {str(e)}")
            if conn:
                conn.close()
            return {}
    
    def list_tables(self) -> List[str]:
        """
        List all tables in the database
        
        Returns:
            List of table names
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            return tables
            
        except Exception as e:
            logger.error(f"Error listing tables: {str(e)}")
            if conn:
                conn.close()
            return []
    
    def export_to_csv(self, table_name: str, output_path: str) -> bool:
        """
        Export table data to CSV file
        
        Args:
            table_name: Name of the table to export
            output_path: Path to save CSV file
            
        Returns:
            True if export successful
        """
        try:
            conn = self._get_connection()
            
            # Sanitize table name
            sanitized_table_name = table_name.lower().replace(' ', '_').replace('-', '_').replace('.', '_')
            sanitized_table_name = ''.join(c for c in sanitized_table_name if c.isalnum() or c == '_')
            
            # Read data into DataFrame
            df = pd.read_sql_query(f"SELECT * FROM {sanitized_table_name}", conn)
            
            # Export to CSV
            df.to_csv(output_path, index=False)
            
            conn.close()
            logger.info(f"Exported {len(df)} records from {sanitized_table_name} to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting {sanitized_table_name} to CSV: {str(e)}")
            if conn:
                conn.close()
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with database statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get all tables
            tables = self.list_tables()
            
            # Get statistics for each table
            table_stats = {}
            total_records = 0
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                record_count = cursor.fetchone()[0]
                table_stats[table] = record_count
                total_records += record_count
            
            conn.close()
            
            return {
                'database_path': self.db_path,
                'total_tables': len(tables),
                'total_records': total_records,
                'table_stats': table_stats,
                'tables': tables
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            if conn:
                conn.close()
            return {}


# Storage manager cache
_storage_managers = {}

def get_storage_manager(db_path: str = None) -> SQLiteStorageManager:
    """Get storage manager instance for the specified database path"""
    if db_path is None:
        db_path = "synthetic_data.db"
    
    # Create new instance for each unique database path
    if db_path not in _storage_managers:
        _storage_managers[db_path] = SQLiteStorageManager(db_path)
    
    return _storage_managers[db_path]
