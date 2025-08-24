# SQLite Integration for Synthetic Data Generation

## Overview

This document describes the new SQLite storage integration feature that allows generated synthetic data to be automatically stored in SQLite database tables. This feature provides a more robust and queryable storage solution compared to CSV files, while maintaining backward compatibility.

## 🚀 Key Features

### Automatic Table Creation
- **Schema-based tables**: Tables are automatically created based on your schema definitions
- **Data type mapping**: Automatic mapping of data types to SQLite-compatible types
- **Constraint handling**: Support for required fields, unique constraints, and data validation

### Flexible Storage Options
- **Multiple storage targets**: Store in SQLite, CSV, or both simultaneously
- **Configurable table names**: Customize table names or use schema names automatically
- **Database path selection**: Choose where to store your SQLite database files

### Data Management
- **Query capabilities**: Query stored data with pagination and filtering
- **Export functionality**: Export tables to CSV format
- **Statistics and monitoring**: Get database and table statistics
- **Data validation**: Track validation status and errors

## 📋 Quick Start

### 1. Basic Usage

```python
from src.synthetic_data_generator import SyntheticDataGenerator
from src.models import SchemaDefinition, FieldDefinition, DataType

# Create generator
generator = SyntheticDataGenerator()

# Define schema
schema = SchemaDefinition(
    name="users",
    fields=[
        FieldDefinition(name="user_id", data_type=DataType.INTEGER, required=True),
        FieldDefinition(name="name", data_type=DataType.NAME, required=True),
        FieldDefinition(name="email", data_type=DataType.EMAIL, required=True),
    ],
    record_count=100
)

# Generate and store in SQLite
results = generator.generate_to_sqlite(
    schema=schema,
    table_name="users",
    db_path="my_data.db"
)

print(f"Generated {len(results['generated_records'])} records")
print(f"Stored in table: {results['table_name']}")
print(f"Database: {results['database_path']}")
```

### 2. Flexible Storage Options

```python
# Store in both SQLite and CSV
results = generator.generate_with_storage_options(
    schema=schema,
    storage_options={
        'save_to_sqlite': True,
        'save_to_csv': True,
        'table_name': 'custom_users',
        'db_path': 'my_data.db',
        'csv_path': 'users.csv'
    }
)
```

### 3. Direct Storage Manager Usage

```python
from src.sqlite_storage import get_storage_manager

# Get storage manager
storage_manager = get_storage_manager("my_data.db")

# Create table from schema
storage_manager.create_table_from_schema("users", schema.dict())

# Insert data
result = storage_manager.insert_data(
    table_name="users",
    data=generated_records,
    schema_definition=schema.dict()
)
```

## 🔧 API Reference

### SyntheticDataGenerator Methods

#### `generate_to_sqlite(schema, table_name=None, db_path=None, **kwargs)`

Generate synthetic data and store directly in SQLite database.

**Parameters:**
- `schema`: SchemaDefinition object
- `table_name`: Name of the table (defaults to schema name)
- `db_path`: Path to SQLite database file
- `**kwargs`: Additional generation parameters

**Returns:**
- Dictionary with generation results and storage information

#### `generate_with_storage_options(schema, storage_options=None, **kwargs)`

Generate data with flexible storage configuration.

**Parameters:**
- `schema`: SchemaDefinition object
- `storage_options`: Dictionary with storage configuration
  - `save_to_sqlite`: bool (default True)
  - `save_to_csv`: bool (default False)
  - `table_name`: str (optional)
  - `db_path`: str (optional)
  - `csv_path`: str (optional)
- `**kwargs`: Additional generation parameters

### SQLiteStorageManager Methods

#### `create_table_from_schema(table_name, schema_definition)`

Create a table based on schema definition.

#### `insert_data(table_name, data, schema_definition=None)`

Insert data into SQLite table.

#### `query_data(table_name, limit=100, offset=0)`

Query data from table with pagination.

#### `get_table_info(table_name)`

Get detailed information about a table.

#### `list_tables()`

List all tables in the database.

#### `export_to_csv(table_name, output_path)`

Export table data to CSV file.

#### `get_database_stats()`

Get comprehensive database statistics.

## 🌐 Web API Endpoints

### SQLite Management Endpoints

#### `GET /api/sqlite/tables`
List all tables in the SQLite database.

**Response:**
```json
{
  "success": true,
  "tables": ["users", "products", "orders"]
}
```

#### `GET /api/sqlite/table/<table_name>`
Get detailed information about a specific table.

**Response:**
```json
{
  "success": true,
  "table_info": {
    "table_name": "users",
    "columns": [...],
    "record_count": 150,
    "sample_data": [...]
  }
}
```

#### `GET /api/sqlite/table/<table_name>/data`
Get data from a table with pagination.

**Parameters:**
- `limit`: Maximum number of records (default: 100)
- `offset`: Number of records to skip (default: 0)

#### `GET /api/sqlite/export/<table_name>`
Export table data as CSV file.

#### `GET /api/sqlite/stats`
Get SQLite database statistics.

### Enhanced Generation Endpoint

The existing `/api/generate` endpoint now supports SQLite storage:

```json
{
  "schema": {...},
  "generation_params": {
    "save_to_sqlite": true,
    "table_name": "custom_table",
    "save_to_database": false
  }
}
```

## 📊 Data Type Mapping

| Schema Data Type | SQLite Data Type | Notes |
|------------------|------------------|-------|
| string/text | TEXT | Default text storage |
| integer/int | INTEGER | Whole numbers |
| float/decimal | REAL | Decimal numbers |
| boolean | INTEGER | Stored as 0/1 |
| date/datetime | TEXT | ISO format strings |
| email | TEXT | Email addresses |
| phone | TEXT | Phone numbers |
| name | TEXT | Person names |
| address | TEXT | Full addresses |
| url | TEXT | URLs |
| uuid | TEXT | UUID strings |

## 🔍 Querying Stored Data

### Basic Queries

```python
# Get all data from a table
data = storage_manager.query_data("users")

# Get with pagination
data = storage_manager.query_data("users", limit=50, offset=100)

# Get table information
info = storage_manager.get_table_info("users")
print(f"Table has {info['record_count']} records")
```

### Using SQLite Directly

```python
import sqlite3

# Connect to database
conn = sqlite3.connect("my_data.db")
cursor = conn.cursor()

# Query data
cursor.execute("SELECT * FROM users WHERE age > 25")
users = cursor.fetchall()

# Complex queries
cursor.execute("""
    SELECT category, COUNT(*) as count, AVG(price) as avg_price 
    FROM products 
    GROUP BY category
""")
stats = cursor.fetchall()

conn.close()
```

## 📈 Data Quality and Validation

### Validation Tracking

Each record stored in SQLite includes:
- **Validation status**: 'valid' or 'invalid'
- **Validation errors**: JSON array of error messages
- **Generation metadata**: Information about how the record was generated

### Quality Metrics

```python
# Get quality metrics for a table
table_info = storage_manager.get_table_info("users")

# Check validation status
cursor.execute("""
    SELECT validation_status, COUNT(*) 
    FROM users 
    GROUP BY validation_status
""")
validation_stats = cursor.fetchall()
```

## 🛠️ Configuration

### Database Path Configuration

```python
# Use default path (synthetic_data.db in current directory)
storage_manager = get_storage_manager()

# Use custom path
storage_manager = get_storage_manager("/path/to/my/database.db")

# Use relative path
storage_manager = get_storage_manager("data/my_app.db")
```

### Table Naming Conventions

- **Automatic naming**: Uses schema name converted to lowercase with underscores
- **Custom naming**: Specify exact table name in storage options
- **Naming rules**: 
  - Lowercase letters
  - Underscores for spaces
  - No special characters

## 🔄 Migration from CSV

### Existing CSV Workflow

```python
# Old way - CSV only
generator = SyntheticDataGenerator()
df = generator.generate_dataframe(schema)
df.to_csv("data.csv", index=False)
```

### New SQLite Workflow

```python
# New way - SQLite storage
generator = SyntheticDataGenerator()
results = generator.generate_to_sqlite(schema, table_name="my_data")

# Still get CSV if needed
storage_manager = get_storage_manager()
storage_manager.export_to_csv("my_data", "data.csv")
```

### Hybrid Approach

```python
# Store in both formats
results = generator.generate_with_storage_options(
    schema=schema,
    storage_options={
        'save_to_sqlite': True,
        'save_to_csv': True,
        'table_name': 'my_data',
        'csv_path': 'data.csv'
    }
)
```

## 📊 Performance Considerations

### Large Datasets

- **Batch processing**: Data is inserted in batches for better performance
- **Indexing**: Consider adding indexes for frequently queried columns
- **Memory usage**: Large datasets are processed efficiently with minimal memory overhead

### Optimization Tips

```python
# For large datasets, use transactions
storage_manager = get_storage_manager("large_dataset.db")

# Enable WAL mode for better concurrency
conn = sqlite3.connect("large_dataset.db")
conn.execute("PRAGMA journal_mode=WAL")
conn.close()
```

## 🔒 Security and Best Practices

### Database Security

- **File permissions**: Ensure database files have appropriate permissions
- **Backup strategy**: Regular backups of SQLite database files
- **Connection management**: Always close database connections properly

### Data Privacy

- **Sensitive data**: Be careful with personally identifiable information
- **Access control**: Limit access to database files
- **Encryption**: Consider SQLite encryption for sensitive data

## 🚨 Troubleshooting

### Common Issues

1. **Table already exists**: The system automatically handles existing tables
2. **Permission errors**: Check file permissions for database directory
3. **Data type errors**: Ensure schema data types are compatible with SQLite
4. **Memory issues**: For very large datasets, consider batch processing

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed SQLite operations
storage_manager = get_storage_manager("debug.db")
```

## 📚 Examples

### Complete Example

See `examples/sqlite_storage_example.py` for a comprehensive demonstration.

### E-commerce Integration

The existing ecommerce example has been updated to use SQLite storage alongside CSV files.

### Web Interface

The Flask web application now includes SQLite management endpoints for browsing and exporting data.

## 🔮 Future Enhancements

### Planned Features

1. **Advanced queries**: SQL query builder interface
2. **Data relationships**: Support for foreign keys and joins
3. **Incremental updates**: Add/update existing data
4. **Data versioning**: Track changes and versions
5. **Advanced indexing**: Automatic index creation for performance
6. **Data compression**: Compress large datasets
7. **Cloud storage**: Integration with cloud databases

### Integration Roadmap

1. **PostgreSQL support**: Extend to PostgreSQL databases
2. **MongoDB support**: NoSQL database integration
3. **Data pipelines**: Integration with data processing frameworks
4. **Real-time updates**: Live data streaming capabilities
5. **Advanced analytics**: Built-in data analysis tools

---

This SQLite integration provides a robust, scalable solution for storing and managing synthetic data while maintaining the simplicity and ease of use of the existing system.
