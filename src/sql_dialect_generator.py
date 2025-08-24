"""
SQL Dialect Generator for different database systems
Generates INSERT statements for MySQL, DB2, SQL Server, Oracle, PostgreSQL
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import json

logger = logging.getLogger(__name__)

class SQLDialectGenerator:
    """Generate SQL INSERT statements for different database dialects"""
    
    SUPPORTED_DIALECTS = {
        'mysql': 'MySQL',
        'postgresql': 'PostgreSQL', 
        'sqlserver': 'SQL Server',
        'oracle': 'Oracle',
        'db2': 'IBM DB2'
    }
    
    def __init__(self, dialect: str = 'mysql'):
        """Initialize with specified dialect"""
        if dialect.lower() not in self.SUPPORTED_DIALECTS:
            raise ValueError(f"Unsupported dialect: {dialect}. Supported: {list(self.SUPPORTED_DIALECTS.keys())}")
        
        self.dialect = dialect.lower()
        logger.info(f"SQL Dialect Generator initialized for {self.SUPPORTED_DIALECTS[self.dialect]}")
    
    def get_quote_char(self) -> str:
        """Get the appropriate quote character for identifiers"""
        quote_chars = {
            'mysql': '`',
            'postgresql': '"',
            'sqlserver': '[',  # or "
            'oracle': '"',
            'db2': '"'
        }
        return quote_chars.get(self.dialect, '"')
    
    def get_closing_quote_char(self) -> str:
        """Get the closing quote character for identifiers"""
        if self.dialect == 'sqlserver':
            return ']'
        return self.get_quote_char()
    
    def quote_identifier(self, identifier: str) -> str:
        """Quote an identifier (table name, column name) appropriately for the dialect"""
        quote_char = self.get_quote_char()
        closing_quote = self.get_closing_quote_char()
        return f"{quote_char}{identifier}{closing_quote}"
    
    def format_value(self, value: Any, data_type: str = None) -> str:
        """Format a value appropriately for the SQL dialect"""
        if value is None:
            return 'NULL'
        
        # Handle different data types
        if isinstance(value, str):
            # Escape single quotes
            escaped_value = value.replace("'", "''")
            return f"'{escaped_value}'"
        
        elif isinstance(value, bool):
            if self.dialect in ['mysql', 'postgresql']:
                return 'TRUE' if value else 'FALSE'
            elif self.dialect == 'sqlserver':
                return '1' if value else '0'
            elif self.dialect == 'oracle':
                return '1' if value else '0'
            elif self.dialect == 'db2':
                return '1' if value else '0'
        
        elif isinstance(value, (int, float)):
            return str(value)
        
        elif isinstance(value, datetime):
            if self.dialect == 'mysql':
                return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
            elif self.dialect == 'postgresql':
                return f"'{value.isoformat()}'"
            elif self.dialect == 'sqlserver':
                return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
            elif self.dialect == 'oracle':
                return f"TO_DATE('{value.strftime('%Y-%m-%d %H:%M:%S')}', 'YYYY-MM-DD HH24:MI:SS')"
            elif self.dialect == 'db2':
                return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
        
        elif isinstance(value, date):
            if self.dialect == 'oracle':
                return f"TO_DATE('{value.strftime('%Y-%m-%d')}', 'YYYY-MM-DD')"
            else:
                return f"'{value.strftime('%Y-%m-%d')}'"
        
        elif isinstance(value, (list, dict)):
            # Handle JSON data
            json_str = json.dumps(value).replace("'", "''")
            if self.dialect == 'postgresql':
                return f"'{json_str}'::json"
            else:
                return f"'{json_str}'"
        
        else:
            # Default: convert to string and quote
            str_value = str(value).replace("'", "''")
            return f"'{str_value}'"
    
    def generate_create_table_if_not_exists(self, table_name: str, schema_definition: Dict) -> str:
        """Generate CREATE TABLE IF NOT EXISTS statement"""
        quoted_table = self.quote_identifier(table_name)
        
        # Build column definitions
        column_defs = []
        fields = schema_definition.get('fields', [])
        
        for field in fields:
            field_name = self.quote_identifier(field['name'])
            field_type = self.map_data_type(field.get('type', 'string'))
            
            # Add constraints
            constraints = []
            if field.get('required', False):
                constraints.append('NOT NULL')
            
            column_def = f"{field_name} {field_type}"
            if constraints:
                column_def += f" {' '.join(constraints)}"
            
            column_defs.append(column_def)
        
        columns_sql = ',\n    '.join(column_defs)
        
        # Generate CREATE TABLE statement based on dialect
        if self.dialect == 'mysql':
            return f"""CREATE TABLE IF NOT EXISTS {quoted_table} (
    {columns_sql}
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"""
        
        elif self.dialect == 'postgresql':
            return f"""CREATE TABLE IF NOT EXISTS {quoted_table} (
    {columns_sql}
);"""
        
        elif self.dialect == 'sqlserver':
            return f"""IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' AND xtype='U')
CREATE TABLE {quoted_table} (
    {columns_sql}
);"""
        
        elif self.dialect == 'oracle':
            return f"""BEGIN
    EXECUTE IMMEDIATE 'CREATE TABLE {quoted_table} (
    {columns_sql}
)';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -955 THEN
            RAISE;
        END IF;
END;"""
        
        elif self.dialect == 'db2':
            return f"""CREATE TABLE {quoted_table} (
    {columns_sql}
);"""
        
        return f"CREATE TABLE {quoted_table} ({columns_sql});"
    
    def map_data_type(self, field_type: str) -> str:
        """Map generic field types to dialect-specific SQL types"""
        type_mappings = {
            'mysql': {
                'string': 'VARCHAR(255)',
                'text': 'TEXT',
                'integer': 'INT',
                'float': 'DECIMAL(10,2)',
                'boolean': 'BOOLEAN',
                'date': 'DATE',
                'datetime': 'DATETIME',
                'email': 'VARCHAR(255)',
                'phone': 'VARCHAR(20)',
                'uuid': 'VARCHAR(36)',
                'json': 'JSON'
            },
            'postgresql': {
                'string': 'VARCHAR(255)',
                'text': 'TEXT',
                'integer': 'INTEGER',
                'float': 'DECIMAL(10,2)',
                'boolean': 'BOOLEAN',
                'date': 'DATE',
                'datetime': 'TIMESTAMP',
                'email': 'VARCHAR(255)',
                'phone': 'VARCHAR(20)',
                'uuid': 'UUID',
                'json': 'JSONB'
            },
            'sqlserver': {
                'string': 'NVARCHAR(255)',
                'text': 'NTEXT',
                'integer': 'INT',
                'float': 'DECIMAL(10,2)',
                'boolean': 'BIT',
                'date': 'DATE',
                'datetime': 'DATETIME2',
                'email': 'NVARCHAR(255)',
                'phone': 'NVARCHAR(20)',
                'uuid': 'UNIQUEIDENTIFIER',
                'json': 'NVARCHAR(MAX)'
            },
            'oracle': {
                'string': 'VARCHAR2(255)',
                'text': 'CLOB',
                'integer': 'NUMBER(10)',
                'float': 'NUMBER(10,2)',
                'boolean': 'NUMBER(1)',
                'date': 'DATE',
                'datetime': 'TIMESTAMP',
                'email': 'VARCHAR2(255)',
                'phone': 'VARCHAR2(20)',
                'uuid': 'VARCHAR2(36)',
                'json': 'CLOB'
            },
            'db2': {
                'string': 'VARCHAR(255)',
                'text': 'CLOB',
                'integer': 'INTEGER',
                'float': 'DECIMAL(10,2)',
                'boolean': 'SMALLINT',
                'date': 'DATE',
                'datetime': 'TIMESTAMP',
                'email': 'VARCHAR(255)',
                'phone': 'VARCHAR(20)',
                'uuid': 'VARCHAR(36)',
                'json': 'CLOB'
            }
        }
        
        dialect_types = type_mappings.get(self.dialect, type_mappings['mysql'])
        return dialect_types.get(field_type.lower(), 'VARCHAR(255)')
    
    def generate_insert_statements(self, table_name: str, records: List[Dict[str, Any]], 
                                 batch_size: int = 100) -> List[str]:
        """Generate INSERT statements for the records"""
        if not records:
            return []
        
        quoted_table = self.quote_identifier(table_name)
        statements = []
        
        # Get column names from first record
        columns = list(records[0].keys())
        quoted_columns = [self.quote_identifier(col) for col in columns]
        columns_sql = ', '.join(quoted_columns)
        
        # Generate INSERT statements in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            if self.dialect in ['mysql', 'postgresql']:
                # Multi-row INSERT
                values_list = []
                for record in batch:
                    values = [self.format_value(record.get(col)) for col in columns]
                    values_list.append(f"({', '.join(values)})")
                
                values_sql = ',\n    '.join(values_list)
                statement = f"INSERT INTO {quoted_table} ({columns_sql}) VALUES\n    {values_sql};"
                statements.append(statement)
            
            else:
                # Individual INSERT statements for other dialects
                for record in batch:
                    values = [self.format_value(record.get(col)) for col in columns]
                    values_sql = ', '.join(values)
                    statement = f"INSERT INTO {quoted_table} ({columns_sql}) VALUES ({values_sql});"
                    statements.append(statement)
        
        return statements
    
    def generate_complete_script(self, table_name: str, schema_definition: Dict, 
                               records: List[Dict[str, Any]]) -> str:
        """Generate complete SQL script with CREATE TABLE and INSERT statements"""
        scripts = []
        
        # Add header comment
        scripts.append(f"-- Generated SQL script for {self.SUPPORTED_DIALECTS[self.dialect]}")
        scripts.append(f"-- Table: {table_name}")
        scripts.append(f"-- Records: {len(records)}")
        scripts.append(f"-- Generated at: {datetime.now().isoformat()}")
        scripts.append("")
        
        # Add CREATE TABLE statement
        create_table_sql = self.generate_create_table_if_not_exists(table_name, schema_definition)
        scripts.append("-- Create table if not exists")
        scripts.append(create_table_sql)
        scripts.append("")
        
        # Add INSERT statements
        if records:
            scripts.append("-- Insert data")
            insert_statements = self.generate_insert_statements(table_name, records)
            scripts.extend(insert_statements)
        
        return '\n'.join(scripts)
    
    def generate_multi_table_script(self, tables_data: Dict[str, Dict]) -> str:
        """Generate complete SQL script for multiple tables"""
        scripts = []
        
        # Add header comment
        scripts.append(f"-- Generated multi-table SQL script for {self.SUPPORTED_DIALECTS[self.dialect]}")
        scripts.append(f"-- Tables: {', '.join(tables_data.keys())}")
        scripts.append(f"-- Generated at: {datetime.now().isoformat()}")
        scripts.append("")
        
        # Process each table
        for table_name, table_info in tables_data.items():
            schema_definition = table_info.get('schema', {})
            records = table_info.get('records', [])
            
            scripts.append(f"-- ========================================")
            scripts.append(f"-- Table: {table_name}")
            scripts.append(f"-- Records: {len(records)}")
            scripts.append(f"-- ========================================")
            scripts.append("")
            
            # CREATE TABLE
            create_table_sql = self.generate_create_table_if_not_exists(table_name, schema_definition)
            scripts.append(create_table_sql)
            scripts.append("")
            
            # INSERT statements
            if records:
                insert_statements = self.generate_insert_statements(table_name, records)
                scripts.extend(insert_statements)
                scripts.append("")
        
        return '\n'.join(scripts)

def get_supported_dialects() -> Dict[str, str]:
    """Get list of supported SQL dialects"""
    return SQLDialectGenerator.SUPPORTED_DIALECTS.copy()
