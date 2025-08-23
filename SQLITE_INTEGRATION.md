# SQLite Integration Guide

## Overview

The Synthetic Data Generator now includes full SQLite database integration, providing persistent storage, data management, and advanced querying capabilities for all generated datasets.

## 🚀 Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Application**
   ```bash
   python app.py
   ```

3. **Access the Web Interface**
   - Open http://localhost:5001 in your browser
   - Navigate to the "Saved Datasets" tab to see stored data

## 📊 Database Features

### Automatic Data Persistence
- **All generated data is automatically saved** to SQLite database
- Each dataset includes metadata, schema definition, and quality metrics
- Individual records are stored with validation status and metadata

### Web Interface Integration
- **Saved Datasets Tab**: Browse and manage all stored datasets
- **Database Statistics**: View total datasets, records, and recent activity
- **Search Functionality**: Find datasets by name or description
- **Export Options**: Download any saved dataset as CSV

### REST API Endpoints

#### Dataset Management
- `GET /api/datasets` - List all saved datasets
- `GET /api/datasets/<id>` - Get dataset details
- `GET /api/datasets/<id>/records` - Get dataset records
- `DELETE /api/datasets/<id>` - Delete dataset and all records

#### Data Export
- `GET /api/datasets/<id>/export/csv` - Export dataset as CSV file

#### Search & Statistics
- `GET /api/datasets/<id>/search?q=<query>` - Search records within dataset
- `GET /api/database/stats` - Get database statistics

## 🗄️ Database Schema

### Tables

#### `datasets` Table
- `id` - Primary key
- `name` - Dataset name
- `description` - Dataset description
- `schema_definition` - JSON schema definition
- `record_count` - Number of records
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp
- `generation_metadata` - JSON generation metadata
- `quality_metrics` - JSON quality metrics

#### `data_records` Table
- `id` - Primary key
- `dataset_id` - Foreign key to datasets
- `record_data` - JSON record data
- `is_valid` - Validation status
- `validation_errors` - JSON validation errors
- `generation_metadata` - JSON generation metadata
- `created_at` - Creation timestamp

## 💡 Usage Examples

### 1. Generate and Save Data
```python
# Using the web interface or API
curl -X POST http://localhost:5001/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "schema": {
      "name": "customer_data",
      "description": "Customer information",
      "fields": [
        {"name": "id", "data_type": "INTEGER", "required": true},
        {"name": "name", "data_type": "STRING", "required": true},
        {"name": "email", "data_type": "EMAIL", "required": true}
      ]
    },
    "generation_params": {
      "record_count": 100,
      "save_to_database": true
    }
  }'
```

### 2. Retrieve Saved Datasets
```python
curl http://localhost:5001/api/datasets
```

### 3. Export Dataset to CSV
```python
curl http://localhost:5001/api/datasets/1/export/csv --output customer_data.csv
```

### 4. Search Within Dataset
```python
curl "http://localhost:5001/api/datasets/1/search?q=john"
```

### 5. Get Database Statistics
```python
curl http://localhost:5001/api/database/stats
```

## 🔧 Configuration

### Database Location
- Default: `sqlite:///synthetic_data.db` in project root
- Configurable via `DatabaseManager(database_url="...")`

### Auto-Save Settings
- **Default**: All generated data is automatically saved
- **Override**: Set `save_to_database: false` in generation parameters

## 📱 Web Interface Features

### Saved Datasets Tab
- **Dataset Cards**: View all saved datasets with metadata
- **Statistics Dashboard**: See total datasets, records, and activity
- **Search Bar**: Filter datasets by name or description
- **Action Buttons**:
  - **View**: Load dataset into Generated Data tab
  - **Export**: Download as CSV file
  - **Delete**: Remove dataset permanently

### Database Statistics
- **Total Datasets**: Number of saved datasets
- **Total Records**: Total number of generated records
- **Last Generated**: Timestamp of most recent dataset

## 🛠️ Advanced Features

### Programmatic Access
```python
from src.database import get_db_manager

# Get database manager
db = get_db_manager()

# Save custom dataset
dataset_id = db.save_dataset(
    name="my_dataset",
    description="Custom dataset",
    schema_definition=schema_dict,
    records=records_list,
    generation_metadata=metadata,
    quality_metrics=metrics
)

# Query datasets
datasets = db.get_datasets(limit=10)
records = db.get_dataset_records(dataset_id, limit=50)

# Search records
results = db.search_records(dataset_id, "search_term")

# Delete dataset
db.delete_dataset(dataset_id)
```

### Database Migration
- SQLite database is created automatically on first run
- Tables are created using SQLAlchemy models
- No manual setup required

## 🔍 Troubleshooting

### Common Issues

#### Database File Permissions
```bash
# Ensure write permissions in project directory
chmod 755 /path/to/project
```

#### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade sqlalchemy flask-sqlalchemy
```

#### Database Corruption
```bash
# Remove database file to reset (loses all data)
rm synthetic_data.db
```

### Debugging

#### Check Database Status
```python
curl http://localhost:5001/api/database/stats
```

#### View Database File
```bash
# Using sqlite3 command line
sqlite3 synthetic_data.db
.tables
.schema datasets
SELECT COUNT(*) FROM datasets;
```

## 📈 Performance Considerations

### Optimization Tips
- **Pagination**: Use `limit` and `offset` for large datasets
- **Indexing**: SQLite automatically indexes primary keys
- **Search**: Text search is case-sensitive and uses LIKE queries
- **Export**: Large datasets may take time to export

### Limits
- **SQLite**: No built-in connection limits
- **File Size**: SQLite can handle databases up to 281TB
- **Concurrent Access**: Multiple readers, single writer

## 🔮 Future Enhancements

### Planned Features
- **Advanced Search**: Full-text search capabilities
- **Data Relationships**: Cross-dataset relationships
- **Backup/Restore**: Database backup and restore tools
- **Analytics**: Advanced dataset analytics and visualizations
- **API Authentication**: Secure API access controls

### Extension Points
- **Custom Exporters**: Additional export formats (JSON, Excel, Parquet)
- **Database Backends**: Support for PostgreSQL, MySQL
- **Data Validation**: Enhanced validation rules and constraints
- **Monitoring**: Performance monitoring and alerting

## 📝 Best Practices

### Dataset Naming
- Use descriptive, unique names
- Include version numbers for evolving schemas
- Follow consistent naming conventions

### Data Management
- Regularly export important datasets
- Monitor database size and performance
- Clean up old or unused datasets

### Security
- Protect database file access in production
- Implement authentication for sensitive data
- Regular backups of critical datasets

## 🎯 Summary

The SQLite integration provides:
- ✅ **Persistent Storage** - All data automatically saved
- ✅ **Web Interface** - Browse and manage datasets visually
- ✅ **REST API** - Programmatic access to all features
- ✅ **Export Options** - Download data in multiple formats
- ✅ **Search Capabilities** - Find specific records quickly
- ✅ **Zero Configuration** - Works out of the box
- ✅ **Performance** - Fast queries and operations
- ✅ **Scalability** - Handles large datasets efficiently

Your synthetic data generation system now has enterprise-grade data management capabilities!
