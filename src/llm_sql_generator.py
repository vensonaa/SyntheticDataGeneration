"""
LLM-based SQL Generator for different database dialects
Uses Groq LLM to generate SQL statements for Oracle, MySQL, SQL Server, DB2, and PostgreSQL
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq

logger = logging.getLogger(__name__)

class LLMSQLGenerator:
    """Generate SQL using LLM for different database dialects"""
    
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
        self.client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        
    def generate_sql_from_data(self, table_name: str, schema_definition: dict, records: List[Dict], 
                              description: str = "") -> str:
        """Generate SQL using LLM based on schema and data"""
        
        # Prepare the prompt for the LLM
        prompt = self._build_prompt(table_name, schema_definition, records, description)
        
        try:
            # Call Groq LLM
            response = self.client.chat.completions.create(
                model="llama3-8b-8192",  # Using Llama model for better SQL generation
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert SQL developer specializing in database-specific syntax and best practices."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                temperature=0.1,  # Low temperature for consistent SQL generation
                max_tokens=4000
            )
            
            sql_content = response.choices[0].message.content.strip()
            
            # Clean up the response - remove markdown code blocks if present
            if sql_content.startswith('```sql'):
                sql_content = sql_content[7:]
            if sql_content.startswith('```'):
                sql_content = sql_content[3:]
            if sql_content.endswith('```'):
                sql_content = sql_content[:-3]
            
            return sql_content.strip()
            
        except Exception as e:
            logger.error(f"Failed to generate SQL with LLM: {str(e)}")
            # Fallback to basic SQL generation
            return self._generate_fallback_sql(table_name, schema_definition, records)
    
    def _build_prompt(self, table_name: str, schema_definition: dict, records: List[Dict], description: str) -> str:
        """Build the prompt for LLM SQL generation"""
        
        dialect_name = self.SUPPORTED_DIALECTS[self.dialect]
        
        # Extract field information from schema
        fields = []
        if 'fields' in schema_definition:
            for field in schema_definition['fields']:
                field_info = f"- {field['name']}: {field['data_type']}"
                if field.get('required', False):
                    field_info += " (NOT NULL)"
                fields.append(field_info)
        elif 'tables' in schema_definition:
            # Multi-table schema
            for table_def in schema_definition['tables']:
                table_fields = []
                for field in table_def.get('fields', []):
                    field_info = f"- {field['name']}: {field['data_type']}"
                    if field.get('required', False):
                        field_info += " (NOT NULL)"
                    table_fields.append(field_info)
                fields.append(f"Table: {table_def['name']}\n" + "\n".join(table_fields))
        
        # Prepare sample data (first 5 records for reference)
        sample_data = []
        for i, record in enumerate(records[:5]):  # Show first 5 records as examples
            if isinstance(record, dict) and 'data' in record:
                sample_data.append(f"Record {i+1}: {json.dumps(record['data'], indent=2)}")
            else:
                sample_data.append(f"Record {i+1}: {json.dumps(record, indent=2)}")
        
        # Prepare all records data for INSERT statements
        all_records_data = []
        for i, record in enumerate(records):
            if isinstance(record, dict) and 'data' in record:
                all_records_data.append(record['data'])
            else:
                all_records_data.append(record)
        
        prompt = f"""
Generate {dialect_name} SQL statements for the following data:

Table Name: {table_name}
Description: {description}

Schema Definition:
{json.dumps(schema_definition, indent=2)}

Fields:
{chr(10).join(fields)}

Sample Data (showing first 5 records as examples):
{chr(10).join(sample_data)}

IMPORTANT: You have {len(records)} total records. Generate INSERT statements for ALL {len(records)} records, not just the sample data shown above.

All Records Data (for generating INSERT statements):
{json.dumps(all_records_data, indent=2)}

Please generate:
1. CREATE TABLE statement with proper {dialect_name} syntax
2. INSERT statements for ALL {len(records)} records from the dataset
3. Use appropriate data types for {dialect_name}
4. Include proper constraints and indexes if needed
5. Use {dialect_name}-specific features where beneficial

Generate only the SQL statements without any explanations or markdown formatting. Make sure to include INSERT statements for all {len(records)} records.
"""
        
        return prompt
    
    def _generate_fallback_sql(self, table_name: str, schema_definition: dict, records: List[Dict]) -> str:
        """Generate basic SQL as fallback when LLM fails"""
        
        # Extract fields
        fields = []
        if 'fields' in schema_definition:
            for field in schema_definition['fields']:
                sql_type = self._map_data_type(field['data_type'])
                field_def = f"{field['name']} {sql_type}"
                if field.get('required', False):
                    field_def += " NOT NULL"
                fields.append(field_def)
        
        # Generate CREATE TABLE
        create_table = f"CREATE TABLE {table_name} (\n"
        create_table += ",\n".join(f"    {field}" for field in fields)
        create_table += "\n);\n\n"
        
        # Generate INSERT statements
        inserts = []
        for record in records:
            if isinstance(record, dict) and 'data' in record:
                data = record['data']
            else:
                data = record
            
            # Extract values in the same order as fields
            values = []
            for field in schema_definition.get('fields', []):
                field_name = field['name']
                value = data.get(field_name, None)  # Use None as default, not 'NULL'
                if value is not None and not isinstance(value, (int, float)):
                    escaped_value = str(value).replace("'", "''")
                    value = f"'{escaped_value}'"
                values.append(str(value) if value is not None else 'NULL')
            
            insert = f"INSERT INTO {table_name} VALUES ({', '.join(values)});"
            inserts.append(insert)
        
        return create_table + "\n".join(inserts)
    
    def _map_data_type(self, data_type: str) -> str:
        """Map generic data types to dialect-specific SQL types"""
        
        type_mapping = {
            'mysql': {
                'STRING': 'VARCHAR(255)',
                'TEXT': 'TEXT',
                'INTEGER': 'INT',
                'FLOAT': 'FLOAT',
                'BOOLEAN': 'BOOLEAN',
                'DATE': 'DATE',
                'DATETIME': 'DATETIME',
                'EMAIL': 'VARCHAR(255)',
                'PHONE': 'VARCHAR(20)',
                'URL': 'VARCHAR(500)'
            },
            'postgresql': {
                'STRING': 'VARCHAR(255)',
                'TEXT': 'TEXT',
                'INTEGER': 'INTEGER',
                'FLOAT': 'REAL',
                'BOOLEAN': 'BOOLEAN',
                'DATE': 'DATE',
                'DATETIME': 'TIMESTAMP',
                'EMAIL': 'VARCHAR(255)',
                'PHONE': 'VARCHAR(20)',
                'URL': 'VARCHAR(500)'
            },
            'sqlserver': {
                'STRING': 'NVARCHAR(255)',
                'TEXT': 'NTEXT',
                'INTEGER': 'INT',
                'FLOAT': 'FLOAT',
                'BOOLEAN': 'BIT',
                'DATE': 'DATE',
                'DATETIME': 'DATETIME2',
                'EMAIL': 'NVARCHAR(255)',
                'PHONE': 'NVARCHAR(20)',
                'URL': 'NVARCHAR(500)'
            },
            'oracle': {
                'STRING': 'VARCHAR2(255)',
                'TEXT': 'CLOB',
                'INTEGER': 'NUMBER(10)',
                'FLOAT': 'NUMBER(10,2)',
                'BOOLEAN': 'NUMBER(1)',
                'DATE': 'DATE',
                'DATETIME': 'TIMESTAMP',
                'EMAIL': 'VARCHAR2(255)',
                'PHONE': 'VARCHAR2(20)',
                'URL': 'VARCHAR2(500)'
            },
            'db2': {
                'STRING': 'VARCHAR(255)',
                'TEXT': 'CLOB',
                'INTEGER': 'INTEGER',
                'FLOAT': 'DOUBLE',
                'BOOLEAN': 'SMALLINT',
                'DATE': 'DATE',
                'DATETIME': 'TIMESTAMP',
                'EMAIL': 'VARCHAR(255)',
                'PHONE': 'VARCHAR(20)',
                'URL': 'VARCHAR(500)'
            }
        }
        
        return type_mapping.get(self.dialect, {}).get(data_type.upper(), 'VARCHAR(255)')


def get_supported_dialects() -> Dict[str, str]:
    """Get list of supported database dialects"""
    return LLMSQLGenerator.SUPPORTED_DIALECTS.copy()
