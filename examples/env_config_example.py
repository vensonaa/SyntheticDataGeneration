#!/usr/bin/env python3
"""
Example: Environment Configuration for Synthetic Data Generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.env_config import EnvConfig, setup_environment
from src.models import SchemaDefinition, FieldDefinition, DataType
from src.genai_data_generator import GenAISyntheticDataGenerator
import pandas as pd


def create_test_schema() -> SchemaDefinition:
    """Create a test schema for demonstration"""
    
    fields = [
        FieldDefinition(
            name="id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=100
        ),
        FieldDefinition(
            name="name",
            data_type=DataType.NAME,
            required=True
        ),
        FieldDefinition(
            name="email",
            data_type=DataType.EMAIL,
            required=True
        ),
        FieldDefinition(
            name="profession",
            data_type=DataType.STRING,
            required=True,
            choices=["Engineer", "Doctor", "Teacher", "Artist", "Manager"]
        ),
        FieldDefinition(
            name="experience_years",
            data_type=DataType.INTEGER,
            required=True,
            min_value=0,
            max_value=30
        )
    ]
    
    return SchemaDefinition(
        name="env_test_data",
        description="Test data for environment configuration demo",
        fields=fields,
        record_count=5  # Small count for demo
    )


def demo_environment_configuration():
    """Demonstrate environment configuration features"""
    
    print("🔧 Environment Configuration Demo")
    print("=" * 50)
    
    # Setup and validate environment
    config = setup_environment()
    
    # Print current configuration
    EnvConfig.print_config()
    
    # Show individual configuration values
    print(f"\n📋 Individual Configuration Values:")
    print(f"   Default Model: {EnvConfig.get_default_model()}")
    print(f"   Default Temperature: {EnvConfig.get_default_temperature()}")
    print(f"   Default Record Count: {EnvConfig.get_default_record_count()}")
    print(f"   Recursion Limit: {EnvConfig.get_recursion_limit()}")
    print(f"   Max Retries: {EnvConfig.get_max_retries()}")
    print(f"   Quality Enhancement: {EnvConfig.is_quality_enhancement_enabled()}")
    print(f"   Contextual Generation: {EnvConfig.is_contextual_generation_enabled()}")
    print(f"   Default Output Format: {EnvConfig.get_default_output_format()}")
    print(f"   CSV Export Enabled: {EnvConfig.is_csv_export_enabled()}")
    
    return config


def demo_generation_with_env_config():
    """Demonstrate generation using environment configuration"""
    
    print(f"\n🚀 Generation with Environment Configuration")
    print("=" * 50)
    
    # Check if API key is available
    api_key = EnvConfig.get_groq_api_key()
    if not api_key:
        print("❌ GROQ_API_KEY not found in .env file")
        print("   Skipping generation demo")
        print("   Please add your API key to the .env file:")
        print("   GROQ_API_KEY=your_actual_api_key_here")
        return
    
    try:
        # Create generator (uses environment defaults)
        print("📦 Creating generator with environment defaults...")
        generator = GenAISyntheticDataGenerator()
        
        # Create schema
        print("📋 Creating test schema...")
        schema = create_test_schema()
        
        # Generate data using environment settings
        print("🔄 Generating data with environment configuration...")
        results = generator.generate_data(schema)
        
        if "error" in results:
            print(f"❌ Generation failed: {results['error']}")
            return
        
        # Display results
        print(f"✅ Generated {len(results['generated_records'])} records")
        
        # Show sample data
        print(f"\n📄 Sample Data:")
        df = pd.DataFrame([record["data"] for record in results["generated_records"][:3]])
        print(df.to_string(index=False))
        
        # Show generation metadata
        metadata = results.get("generation_metadata", {})
        print(f"\n📊 Generation Metadata:")
        print(f"   Model Used: {metadata.get('model_name', 'N/A')}")
        print(f"   Generation Method: {metadata.get('generation_method', 'N/A')}")
        print(f"   LLM Provider: {metadata.get('llm_provider', 'N/A')}")
        print(f"   Quality Enhancements: {metadata.get('quality_enhancements', 0)}")
        
        # Show quality metrics
        quality_metrics = results.get("quality_metrics", {})
        print(f"\n📈 Quality Metrics:")
        print(f"   Completeness: {quality_metrics.get('completeness', 0):.1f}%")
        print(f"   Validity: {quality_metrics.get('validity', 0):.1f}%")
        print(f"   Total Records: {quality_metrics.get('total_records', 0)}")
        
    except Exception as e:
        print(f"❌ Generation demo failed: {e}")


def demo_environment_override():
    """Demonstrate overriding environment settings"""
    
    print(f"\n⚙️ Environment Override Demo")
    print("=" * 50)
    
    # Show how to override environment settings
    print("📝 You can override environment settings in your code:")
    print()
    
    print("1. Override model and temperature:")
    print("   generator = GenAISyntheticDataGenerator(model_name='llama3-70b-8192')")
    print("   results = generator.generate_data(schema, temperature=0.8)")
    print()
    
    print("2. Override generation settings:")
    print("   results = generator.generate_data(")
    print("       schema,")
    print("       use_contextual_generation=False,")
    print("       quality_enhancement=False")
    print("   )")
    print()
    
    print("3. Override record count:")
    print("   schema.record_count = 100  # Override env default")
    print()
    
    print("4. Override recursion limit:")
    print("   final_state = app.invoke(initial_state, config={'recursion_limit': 500})")


def demo_environment_file_management():
    """Demonstrate .env file management"""
    
    print(f"\n📁 .env File Management")
    print("=" * 50)
    
    print("📋 Your .env file should contain:")
    print()
    print("# Groq API Configuration")
    print("GROQ_API_KEY=your_actual_api_key_here")
    print()
    print("# Generation Settings")
    print("DEFAULT_RECORD_COUNT=1000")
    print("DEFAULT_BATCH_SIZE=10")
    print()
    print("# Model Configuration")
    print("DEFAULT_GROQ_MODEL=llama3-8b-8192")
    print("DEFAULT_TEMPERATURE=0.5")
    print()
    print("# Quality Settings")
    print("ENABLE_QUALITY_ENHANCEMENT=true")
    print("ENABLE_CONTEXTUAL_GENERATION=true")
    print()
    print("# Performance Settings")
    print("RECURSION_LIMIT=200")
    print("MAX_RETRIES=3")
    print()
    print("# Output Settings")
    print("DEFAULT_OUTPUT_FORMAT=json")
    print("ENABLE_CSV_EXPORT=true")
    
    print(f"\n💡 Tips:")
    print(f"   - Never commit your .env file to version control")
    print(f"   - Use .env.example for sharing configuration structure")
    print(f"   - Different environments can have different .env files")
    print(f"   - Environment variables take precedence over .env file")


def main():
    """Main demonstration function"""
    
    print("🚀 Environment Configuration for Synthetic Data Generation")
    print("=" * 70)
    print("This demo shows how to use .env files for configuration management.")
    print()
    
    try:
        # Demo environment configuration
        config = demo_environment_configuration()
        
        # Demo generation with environment config
        demo_generation_with_env_config()
        
        # Demo environment override
        demo_environment_override()
        
        # Demo .env file management
        demo_environment_file_management()
        
        print(f"\n🎉 Environment configuration demo completed!")
        
        print(f"\n📋 Next Steps:")
        print(f"   1. Edit your .env file with your actual Groq API key")
        print(f"   2. Customize other settings as needed")
        print(f"   3. Run: python examples/genai_example.py")
        print(f"   4. Or run: python examples/groq_example.py")
        
        print(f"\n💡 Benefits of .env Configuration:")
        print(f"   ✅ Centralized configuration management")
        print(f"   ✅ Environment-specific settings")
        print(f"   ✅ Secure API key storage")
        print(f"   ✅ Easy deployment across environments")
        print(f"   ✅ No hardcoded values in code")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print(f"💡 Make sure you have a .env file in the project root")


if __name__ == "__main__":
    main()
