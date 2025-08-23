#!/usr/bin/env python3
"""
Example: Generate synthetic user data using LangGraph-based synthetic data generator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SchemaDefinition, FieldDefinition, DataType
from src.synthetic_data_generator import SyntheticDataGenerator
import pandas as pd


def create_user_schema() -> SchemaDefinition:
    """Create a schema for user data"""
    
    fields = [
        FieldDefinition(
            name="user_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=10000
        ),
        FieldDefinition(
            name="first_name",
            data_type=DataType.NAME,
            required=True,
            min_length=2,
            max_length=50
        ),
        FieldDefinition(
            name="last_name",
            data_type=DataType.NAME,
            required=True,
            min_length=2,
            max_length=50
        ),
        FieldDefinition(
            name="email",
            data_type=DataType.EMAIL,
            required=True
        ),
        FieldDefinition(
            name="phone",
            data_type=DataType.PHONE,
            required=False
        ),
        FieldDefinition(
            name="address",
            data_type=DataType.ADDRESS,
            required=False
        ),
        FieldDefinition(
            name="age",
            data_type=DataType.INTEGER,
            required=True,
            min_value=18,
            max_value=100
        ),
        FieldDefinition(
            name="is_active",
            data_type=DataType.BOOLEAN,
            required=True
        ),
        FieldDefinition(
            name="registration_date",
            data_type=DataType.DATE,
            required=True
        ),
        FieldDefinition(
            name="subscription_type",
            data_type=DataType.STRING,
            required=True,
            choices=["free", "basic", "premium", "enterprise"]
        ),
        FieldDefinition(
            name="monthly_spend",
            data_type=DataType.FLOAT,
            required=False,
            min_value=0.0,
            max_value=10000.0
        )
    ]
    
    return SchemaDefinition(
        name="user_data",
        description="Synthetic user data for testing",
        fields=fields,
        record_count=50
    )


def main():
    """Main function to demonstrate synthetic data generation"""
    
    print("🚀 Starting Synthetic Data Generation Example")
    print("=" * 50)
    
    # Create the generator
    generator = SyntheticDataGenerator(graph_type="standard")
    
    # Create schema
    schema = create_user_schema()
    
    # Validate schema
    print("📋 Validating schema...")
    validation = generator.validate_schema(schema)
    
    if not validation["is_valid"]:
        print("❌ Schema validation failed:")
        for error in validation["errors"]:
            print(f"   - {error}")
        return
    
    if validation["warnings"]:
        print("⚠️  Schema warnings:")
        for warning in validation["warnings"]:
            print(f"   - {warning}")
    
    print("✅ Schema is valid!")
    
    # Generate data
    print("\n🔄 Generating synthetic user data...")
    results = generator.generate_data(schema)
    
    if "error" in results:
        print(f"❌ Generation failed: {results['error']}")
        return
    
    # Display results
    print(f"✅ Generated {len(results['generated_records'])} records")
    
    # Show quality metrics
    quality_metrics = results["quality_metrics"]
    print(f"\n📊 Quality Metrics:")
    print(f"   - Completeness: {quality_metrics.get('completeness', 0):.1f}%")
    print(f"   - Validity: {quality_metrics.get('validity', 0):.1f}%")
    
    # Show sample data
    print(f"\n📄 Sample Data (first 5 records):")
    df = pd.DataFrame([record["data"] for record in results["generated_records"][:5]])
    print(df.to_string(index=False))
    
    # Save to CSV
    output_file = "generated_user_data.csv"
    generator.generate_csv(schema, output_file)
    print(f"\n💾 Data saved to: {output_file}")
    
    # Generate quality report
    print("\n📈 Generating detailed quality report...")
    quality_report = generator.get_quality_report(results)
    
    print(f"📊 Detailed Quality Report:")
    print(f"   - Total Records: {quality_report.get('total_records', 0)}")
    print(f"   - Completeness: {quality_report.get('completeness', 0):.1f}%")
    print(f"   - Validity: {quality_report.get('validity', 0):.1f}%")
    
    # Show field statistics
    field_stats = quality_report.get("field_statistics", {})
    print(f"\n📋 Field Statistics:")
    for field_name, stats in field_stats.items():
        print(f"   - {field_name}: {stats['filled_count']}/{stats['filled_count'] + stats['null_count']} filled")
    
    print("\n🎉 Synthetic data generation completed successfully!")


if __name__ == "__main__":
    main()
