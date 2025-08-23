#!/usr/bin/env python3
"""
Example: Using GenAI-enhanced synthetic data generation
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SchemaDefinition, FieldDefinition, DataType
from src.genai_data_generator import GenAISyntheticDataGenerator
import pandas as pd


def create_genai_user_schema() -> SchemaDefinition:
    """Create a schema optimized for GenAI generation"""
    
    fields = [
        FieldDefinition(
            name="user_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=10000
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
            name="age",
            data_type=DataType.INTEGER,
            required=True,
            min_value=18,
            max_value=100
        ),
        FieldDefinition(
            name="profession",
            data_type=DataType.STRING,
            required=True,
            choices=["Engineer", "Designer", "Manager", "Analyst", "Consultant", "Teacher", "Doctor", "Artist"]
        ),
        FieldDefinition(
            name="bio",
            data_type=DataType.STRING,
            required=False
        ),
        FieldDefinition(
            name="interests",
            data_type=DataType.STRING,
            required=False
        ),
        FieldDefinition(
            name="is_premium",
            data_type=DataType.BOOLEAN,
            required=True
        )
    ]
    
    return SchemaDefinition(
        name="genai_user_data",
        description="GenAI-enhanced user data with contextual relationships",
        fields=fields,
        record_count=25
    )


def create_product_review_schema() -> SchemaDefinition:
    """Create a schema for product reviews with GenAI enhancement"""
    
    fields = [
        FieldDefinition(
            name="review_id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=10000
        ),
        FieldDefinition(
            name="product_name",
            data_type=DataType.STRING,
            required=True
        ),
        FieldDefinition(
            name="category",
            data_type=DataType.STRING,
            required=True,
            choices=["Electronics", "Books", "Clothing", "Home", "Sports"]
        ),
        FieldDefinition(
            name="rating",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=5
        ),
        FieldDefinition(
            name="review_text",
            data_type=DataType.STRING,
            required=True
        ),
        FieldDefinition(
            name="reviewer_name",
            data_type=DataType.NAME,
            required=True
        ),
        FieldDefinition(
            name="helpful_votes",
            data_type=DataType.INTEGER,
            required=True,
            min_value=0,
            max_value=100
        )
    ]
    
    return SchemaDefinition(
        name="product_reviews",
        description="Product reviews with contextually appropriate content",
        fields=fields,
        record_count=30
    )


def demo_basic_genai_generation():
    """Demonstrate basic GenAI-enhanced data generation"""
    
    print("🤖 GenAI-Enhanced Synthetic Data Generation")
    print("=" * 50)
    
    # Create generator (will use environment defaults)
    generator = GenAISyntheticDataGenerator()
    
    # Create schema
    schema = create_genai_user_schema()
    
    print("📋 Generating GenAI-enhanced user data...")
    
    # Generate data with contextual awareness
    results = generator.generate_data(
        schema,
        use_contextual_generation=True,
        quality_enhancement=True,
        adaptive_strategy=True,
        target_audience="tech professionals",
        data_theme="professional networking"
    )
    
    if "error" in results:
        print(f"❌ Generation failed: {results['error']}")
        return
    
    # Display results
    print(f"✅ Generated {len(results['generated_records'])} records")
    
    # Show generation insights
    insights = generator.get_generation_insights(results)
    print(f"\n🔍 Generation Insights:")
    print(f"   - Method: {insights['generation_method']}")
    print(f"   - LLM Provider: {insights['llm_provider']}")
    print(f"   - Model: {insights['model_used']}")
    print(f"   - LLM Adaptations: {insights['llm_adaptations']}")
    print(f"   - Quality Enhancements: {insights['quality_enhancements']}")
    print(f"   - Enhancement Rate: {insights['enhancement_rate']:.1f}%")
    
    # Show sample data
    df = generator.generate_dataframe(schema,
                                     use_contextual_generation=True,
                                     quality_enhancement=True)
    
    print(f"\n📄 Sample GenAI Data (first 3 records):")
    if not df.empty:
        print(df.head(3).to_string(index=False))
    
    return results


def demo_persona_based_generation():
    """Demonstrate persona-based data generation"""
    
    print(f"\n👥 Persona-Based Data Generation")
    print("=" * 50)
    
    # Define personas
    personas = [
        {
            "name": "Tech Professional",
            "characteristics": {
                "industry": "technology",
                "experience_level": "senior",
                "interests": "AI, programming, innovation"
            },
            "demographics": {
                "age_range": "25-40",
                "education": "university",
                "location": "urban"
            }
        },
        {
            "name": "Creative Professional",
            "characteristics": {
                "industry": "creative",
                "experience_level": "mid-level",
                "interests": "design, art, storytelling"
            },
            "demographics": {
                "age_range": "22-35",
                "education": "art_school",
                "location": "urban"
            }
        },
        {
            "name": "Healthcare Worker",
            "characteristics": {
                "industry": "healthcare",
                "experience_level": "experienced",
                "interests": "wellness, science, helping others"
            },
            "demographics": {
                "age_range": "28-45",
                "education": "medical",
                "location": "suburban"
            }
        }
    ]
    
    generator = GenAISyntheticDataGenerator()
    schema = create_genai_user_schema()
    
    print("🎭 Generating data with personas...")
    results = generator.generate_with_personas(
        schema,
        personas,
        use_contextual_generation=True,
        quality_enhancement=True
    )
    
    if "error" not in results:
        print(f"✅ Generated {len(results['generated_records'])} records across {len(personas)} personas")
        
        # Show persona distribution
        persona_counts = {}
        for record in results["generated_records"]:
            if isinstance(record, dict):
                persona_info = record.get("persona_info", "Unknown")
                persona_counts[persona_info] = persona_counts.get(persona_info, 0) + 1
        
        print(f"\n📊 Persona Distribution:")
        for persona, count in persona_counts.items():
            print(f"   - {persona}: {count} records")
    else:
        print(f"❌ Persona generation failed: {results['error']}")


def demo_product_reviews():
    """Demonstrate contextual product review generation"""
    
    print(f"\n📝 Contextual Product Review Generation")
    print("=" * 50)
    
    generator = GenAISyntheticDataGenerator()
    schema = create_product_review_schema()
    
    print("🛍️ Generating contextual product reviews...")
    results = generator.generate_data(
        schema,
        use_contextual_generation=True,
        quality_enhancement=True,
        review_style="detailed and helpful",
        sentiment_distribution="mostly_positive"
    )
    
    if "error" not in results:
        print(f"✅ Generated {len(results['generated_records'])} product reviews")
        
        # Show quality metrics
        quality_metrics = results.get("quality_metrics", {})
        print(f"\n📊 Quality Metrics:")
        print(f"   - Completeness: {quality_metrics.get('completeness', 0):.1f}%")
        print(f"   - Validity: {quality_metrics.get('validity', 0):.1f}%")
        
        # Show sample reviews
        df = pd.DataFrame([
            record.get("data", record) if isinstance(record, dict) else record 
            for record in results["generated_records"][:3]
        ])
        
        print(f"\n📄 Sample Reviews:")
        if not df.empty:
            for idx, row in df.head(3).iterrows():
                print(f"\n   Review {idx + 1}:")
                print(f"   Product: {row.get('product_name', 'N/A')}")
                print(f"   Rating: {row.get('rating', 'N/A')}/5")
                print(f"   Review: {row.get('review_text', 'N/A')[:100]}...")
    else:
        print(f"❌ Review generation failed: {results['error']}")


def main():
    """Main demonstration function"""
    
    try:
        # Basic GenAI generation
        demo_basic_genai_generation()
        
        # Persona-based generation
        demo_persona_based_generation()
        
        # Product review generation
        demo_product_reviews()
        
        print(f"\n🎉 GenAI demonstration completed!")
        
        print(f"\n💡 GenAI Benefits:")
        print(f"   - Contextually aware data generation")
        print(f"   - Realistic relationships between fields")
        print(f"   - Adaptive quality improvement")
        print(f"   - Persona-based customization")
        print(f"   - Domain-specific intelligence")
        
    except ImportError as e:
        print(f"⚠️ Note: GenAI features require additional dependencies:")
        print(f"   pip install langchain-groq")
        print(f"   Set GROQ_API_KEY in your .env file")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ GenAI demonstration failed: {e}")
        print(f"💡 This might be due to missing API keys or network issues")


if __name__ == "__main__":
    main()
