#!/usr/bin/env python3
"""
SQLite Storage Example for Synthetic Data Generation

This example demonstrates how to use the new SQLite storage functionality
to automatically store generated synthetic data in SQLite database tables.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.synthetic_data_generator import SyntheticDataGenerator
from src.models import SchemaDefinition, FieldDefinition, DataType
from src.sqlite_storage import get_storage_manager
import pandas as pd


def create_user_schema():
    """Create a user data schema"""
    return SchemaDefinition(
        name="users",
        description="Synthetic user profiles",
        fields=[
            FieldDefinition(name="user_id", data_type=DataType.INTEGER, required=True),
            FieldDefinition(name="first_name", data_type=DataType.NAME, required=True),
            FieldDefinition(name="last_name", data_type=DataType.NAME, required=True),
            FieldDefinition(name="email", data_type=DataType.EMAIL, required=True),
            FieldDefinition(name="age", data_type=DataType.INTEGER, required=True, min_value=18, max_value=80),
            FieldDefinition(name="phone", data_type=DataType.PHONE, required=False),
            FieldDefinition(name="address", data_type=DataType.ADDRESS, required=False),
            FieldDefinition(name="registration_date", data_type=DataType.DATE, required=True),
            FieldDefinition(name="is_active", data_type=DataType.BOOLEAN, required=True)
        ],
        record_count=50
    )


def create_product_schema():
    """Create a product data schema"""
    return SchemaDefinition(
        name="products",
        description="E-commerce product catalog",
        fields=[
            FieldDefinition(name="product_id", data_type=DataType.INTEGER, required=True),
            FieldDefinition(name="product_name", data_type=DataType.STRING, required=True, max_length=100),
            FieldDefinition(name="category", data_type=DataType.STRING, required=True, 
                          choices=['Electronics', 'Clothing', 'Books', 'Home', 'Sports']),
            FieldDefinition(name="price", data_type=DataType.FLOAT, required=True, min_value=0.01, max_value=10000),
            FieldDefinition(name="stock_quantity", data_type=DataType.INTEGER, required=True, min_value=0, max_value=1000),
            FieldDefinition(name="description", data_type=DataType.STRING, required=False, max_length=500),
            FieldDefinition(name="created_date", data_type=DataType.DATE, required=True),
            FieldDefinition(name="is_featured", data_type=DataType.BOOLEAN, required=True)
        ],
        record_count=30
    )


def demonstrate_sqlite_storage():
    """Demonstrate SQLite storage functionality"""
    print("🚀 SQLite Storage Example for Synthetic Data Generation")
    print("=" * 60)
    
    # Initialize generator and storage manager
    generator = SyntheticDataGenerator()
    storage_manager = get_storage_manager("example_sqlite.db")
    
    print(f"📊 Using SQLite database: {storage_manager.db_path}")
    print()
    
    # Example 1: Generate and store user data
    print("👥 Example 1: Generating and storing user data")
    print("-" * 40)
    
    user_schema = create_user_schema()
    print(f"Schema: {user_schema.name} ({user_schema.record_count} records)")
    
    # Method 1: Use the new generate_to_sqlite method
    print("\n📝 Method 1: Using generate_to_sqlite()")
    user_results = generator.generate_to_sqlite(
        schema=user_schema,
        table_name="users",
        db_path="example_sqlite.db"
    )
    
    if "error" in user_results:
        print(f"❌ Error: {user_results['error']}")
        return
    
    print(f"✅ Generated {len(user_results['generated_records'])} user records")
    print(f"🗄️ Stored in table: {user_results['table_name']}")
    print(f"💾 Database: {user_results['database_path']}")
    
    storage_result = user_results.get('storage_result', {})
    if storage_result.get('success'):
        print(f"✅ Successfully inserted {storage_result['inserted_count']} records")
    else:
        print(f"❌ Storage failed: {storage_result.get('message', 'Unknown error')}")
    
    print()
    
    # Example 2: Generate and store product data
    print("🛍️ Example 2: Generating and storing product data")
    print("-" * 40)
    
    product_schema = create_product_schema()
    print(f"Schema: {product_schema.name} ({product_schema.record_count} records)")
    
    # Method 2: Use the flexible storage options method
    print("\n📝 Method 2: Using generate_with_storage_options()")
    product_results = generator.generate_with_storage_options(
        schema=product_schema,
        storage_options={
            'save_to_sqlite': True,
            'save_to_csv': True,
            'table_name': 'products',
            'db_path': 'example_sqlite.db',
            'csv_path': 'generated_products_sqlite.csv'
        }
    )
    
    if "error" in product_results:
        print(f"❌ Error: {product_results['error']}")
        return
    
    print(f"✅ Generated {len(product_results['generated_records'])} product records")
    
    storage_results = product_results.get('storage_results', {})
    
    if 'sqlite' in storage_results:
        sqlite_result = storage_results['sqlite']
        if sqlite_result.get('success'):
            print(f"🗄️ SQLite: Inserted {sqlite_result['inserted_count']} records into 'products' table")
        else:
            print(f"❌ SQLite storage failed: {sqlite_result.get('message', 'Unknown error')}")
    
    if 'csv' in storage_results:
        csv_result = storage_results['csv']
        if csv_result.get('success'):
            print(f"📄 CSV: Saved {csv_result['record_count']} records to {csv_result['file_path']}")
        else:
            print(f"❌ CSV export failed")
    
    print()
    
    # Example 3: Query and display stored data
    print("🔍 Example 3: Querying stored data")
    print("-" * 40)
    
    # Get database statistics
    stats = storage_manager.get_database_stats()
    print(f"📊 Database Statistics:")
    print(f"   - Total tables: {stats['total_tables']}")
    print(f"   - Total records: {stats['total_records']}")
    print(f"   - Tables: {', '.join(stats['tables'])}")
    
    # Get table information
    for table_name in stats['tables']:
        print(f"\n📋 Table: {table_name}")
        table_info = storage_manager.get_table_info(table_name)
        print(f"   - Records: {table_info['record_count']}")
        print(f"   - Columns: {len(table_info['columns'])}")
        
        # Show sample data
        sample_data = storage_manager.query_data(table_name, limit=3)
        if sample_data:
            print(f"   - Sample data:")
            for i, record in enumerate(sample_data[:2], 1):
                # Show key fields only
                key_fields = {k: v for k, v in record.items() 
                            if k in ['id', 'user_id', 'product_id', 'first_name', 'product_name', 'email']}
                print(f"     {i}. {key_fields}")
    
    print()
    
    # Example 4: Export data from SQLite
    print("📤 Example 4: Exporting data from SQLite")
    print("-" * 40)
    
    for table_name in stats['tables']:
        csv_filename = f"exported_{table_name}.csv"
        success = storage_manager.export_to_csv(table_name, csv_filename)
        if success:
            print(f"✅ Exported {table_name} to {csv_filename}")
        else:
            print(f"❌ Failed to export {table_name}")
    
    print()
    
    # Example 5: Demonstrate data quality
    print("📈 Example 5: Data Quality Analysis")
    print("-" * 40)
    
    for table_name in stats['tables']:
        print(f"\n📊 Quality metrics for {table_name}:")
        
        # Get table data
        data = storage_manager.query_data(table_name, limit=1000)
        if not data:
            continue
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(data)
        
        # Basic statistics
        print(f"   - Total records: {len(df)}")
        print(f"   - Columns: {len(df.columns)}")
        
        # Check for null values
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            print(f"   - Null values found:")
            for col, count in null_counts[null_counts > 0].items():
                print(f"     * {col}: {count}")
        else:
            print(f"   - No null values found")
        
        # Show data types
        print(f"   - Data types:")
        for col, dtype in df.dtypes.items():
            print(f"     * {col}: {dtype}")
    
    print("\n🎉 SQLite storage example completed successfully!")
    print(f"📁 Database file: {storage_manager.db_path}")
    print(f"📄 Exported CSV files: exported_*.csv")


if __name__ == "__main__":
    demonstrate_sqlite_storage()
