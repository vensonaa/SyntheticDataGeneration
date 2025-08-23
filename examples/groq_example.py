#!/usr/bin/env python3
"""
Example: Using Groq for synthetic data generation
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SchemaDefinition, FieldDefinition, DataType
from src.genai_data_generator import GenAISyntheticDataGenerator
from src.groq_config import GroqConfig, GroqOptimizer
import pandas as pd


def create_groq_test_schema() -> SchemaDefinition:
    """Create a schema for testing Groq models"""
    
    fields = [
        FieldDefinition(
            name="id",
            data_type=DataType.INTEGER,
            required=True,
            min_value=1,
            max_value=1000
        ),
        FieldDefinition(
            name="name",
            data_type=DataType.NAME,
            required=True
        ),
        FieldDefinition(
            name="profession",
            data_type=DataType.STRING,
            required=True,
            choices=["Software Engineer", "Data Scientist", "Product Manager", "Designer", "Marketing Specialist"]
        ),
        FieldDefinition(
            name="bio",
            data_type=DataType.STRING,
            required=False
        ),
        FieldDefinition(
            name="skills",
            data_type=DataType.STRING,
            required=False
        ),
        FieldDefinition(
            name="experience_years",
            data_type=DataType.INTEGER,
            required=True,
            min_value=0,
            max_value=20
        ),
        FieldDefinition(
            name="is_remote",
            data_type=DataType.BOOLEAN,
            required=True
        )
    ]
    
    return SchemaDefinition(
        name="groq_test_data",
        description="Test data for Groq model comparison",
        fields=fields,
        record_count=10
    )


def test_groq_models():
    """Test different Groq models and compare performance"""
    
    print("🚀 Groq Model Performance Comparison")
    print("=" * 50)
    
    schema = create_groq_test_schema()
    
    # Test different models
    models_to_test = [
        "llama3-8b-8192",      # Fast and efficient
        "llama3-70b-8192",     # High quality
        "mixtral-8x7b-32768",  # Large context
        "gemma2-9b-it"         # Instruction-tuned
    ]
    
    results = {}
    
    for model_name in models_to_test:
        print(f"\n🔄 Testing {model_name}...")
        
        try:
            # Create generator with specific model
            generator = GenAISyntheticDataGenerator(model_name=model_name)
            
            # Measure generation time
            start_time = time.time()
            generation_results = generator.generate_data(
                schema,
                use_contextual_generation=True,
                quality_enhancement=True
            )
            end_time = time.time()
            
            generation_time = end_time - start_time
            
            if "error" not in generation_results:
                # Calculate metrics
                record_count = len(generation_results["generated_records"])
                quality_metrics = generation_results.get("quality_metrics", {})
                
                results[model_name] = {
                    "success": True,
                    "generation_time": generation_time,
                    "record_count": record_count,
                    "completeness": quality_metrics.get("completeness", 0),
                    "validity": quality_metrics.get("validity", 0),
                    "records_per_second": record_count / generation_time if generation_time > 0 else 0
                }
                
                print(f"✅ {model_name} completed:")
                print(f"   - Time: {generation_time:.2f}s")
                print(f"   - Records: {record_count}")
                print(f"   - Speed: {results[model_name]['records_per_second']:.1f} records/s")
                print(f"   - Quality: {quality_metrics.get('completeness', 0):.1f}% complete, {quality_metrics.get('validity', 0):.1f}% valid")
                
            else:
                results[model_name] = {
                    "success": False,
                    "error": generation_results["error"]
                }
                print(f"❌ {model_name} failed: {generation_results['error']}")
                
        except Exception as e:
            results[model_name] = {
                "success": False,
                "error": str(e)
            }
            print(f"❌ {model_name} failed: {e}")
    
    # Summary comparison
    print(f"\n📊 Groq Model Comparison Summary")
    print("=" * 50)
    
    successful_results = {k: v for k, v in results.items() if v["success"]}
    
    if successful_results:
        print(f"{'Model':<20} {'Time (s)':<10} {'Records/s':<12} {'Quality':<10}")
        print("-" * 60)
        
        for model_name, result in successful_results.items():
            quality_score = (result["completeness"] + result["validity"]) / 2
            print(f"{model_name:<20} {result['generation_time']:<10.2f} {result['records_per_second']:<12.1f} {quality_score:<10.1f}%")
        
        # Find best performers
        fastest = min(successful_results.items(), key=lambda x: x[1]["generation_time"])
        highest_quality = max(successful_results.items(), key=lambda x: (x[1]["completeness"] + x[1]["validity"]) / 2)
        fastest_speed = max(successful_results.items(), key=lambda x: x[1]["records_per_second"])
        
        print(f"\n🏆 Performance Summary:")
        print(f"   - Fastest Generation: {fastest[0]} ({fastest[1]['generation_time']:.2f}s)")
        print(f"   - Highest Quality: {highest_quality[0]} ({(highest_quality[1]['completeness'] + highest_quality[1]['validity']) / 2:.1f}%)")
        print(f"   - Highest Speed: {fastest_speed[0]} ({fastest_speed[1]['records_per_second']:.1f} records/s)")
    
    return results


def demo_groq_optimization():
    """Demonstrate Groq optimization techniques"""
    
    print(f"\n⚡ Groq Optimization Techniques")
    print("=" * 50)
    
    # Test prompt optimization
    original_prompt = """Generate a detailed product description for a new smartphone that includes all the technical specifications, features, and benefits. Make sure to include information about the camera quality, battery life, processor speed, storage options, and any unique features that set it apart from competitors. The description should be comprehensive and informative."""
    
    optimized_prompt = GroqOptimizer.optimize_prompt_for_groq(original_prompt)
    
    print("📝 Prompt Optimization:")
    print(f"Original length: {len(original_prompt)} characters")
    print(f"Optimized length: {len(optimized_prompt)} characters")
    print(f"Token estimate: {GroqOptimizer.estimate_tokens(optimized_prompt)} tokens")
    
    # Test chunking
    large_text = "This is a very long text. " * 1000  # Create a large text
    chunks = GroqOptimizer.chunk_large_inputs(large_text, max_tokens=1000)
    
    print(f"\n📦 Text Chunking:")
    print(f"Original text: {GroqOptimizer.estimate_tokens(large_text)} tokens")
    print(f"Chunked into: {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"   Chunk {i+1}: {GroqOptimizer.estimate_tokens(chunk)} tokens")
    
    # Model recommendations
    print(f"\n🎯 Model Recommendations:")
    use_cases = ["speed", "quality", "context", "structured"]
    for use_case in use_cases:
        recommended = GroqConfig.recommend_model(use_case)
        model_info = GroqConfig.get_model_info(recommended)
        print(f"   {use_case.capitalize()}: {recommended} - {model_info.get('description', 'N/A')}")


def demo_groq_temperature_effects():
    """Demonstrate how temperature affects generation quality"""
    
    print(f"\n🌡️ Temperature Effects on Generation")
    print("=" * 50)
    
    schema = create_groq_test_schema()
    schema.record_count = 5  # Smaller dataset for testing
    
    temperatures = [0.1, 0.3, 0.5, 0.7, 0.9]
    results = {}
    
    for temp in temperatures:
        print(f"\n🌡️ Testing temperature {temp}...")
        
        try:
            # Create generator with specific temperature
            generator = GenAISyntheticDataGenerator(model_name="llama3-8b-8192")
            
            # Override temperature in context
            generation_results = generator.generate_data(
                schema,
                use_contextual_generation=True,
                temperature=temp
            )
            
            if "error" not in generation_results:
                quality_metrics = generation_results.get("quality_metrics", {})
                results[temp] = {
                    "completeness": quality_metrics.get("completeness", 0),
                    "validity": quality_metrics.get("validity", 0),
                    "sample_data": generation_results["generated_records"][0] if generation_results["generated_records"] else None
                }
                
                print(f"   Quality: {quality_metrics.get('completeness', 0):.1f}% complete, {quality_metrics.get('validity', 0):.1f}% valid")
            else:
                results[temp] = {"error": generation_results["error"]}
                print(f"   Error: {generation_results['error']}")
                
        except Exception as e:
            results[temp] = {"error": str(e)}
            print(f"   Error: {e}")
    
    # Show temperature comparison
    print(f"\n📊 Temperature Comparison:")
    print(f"{'Temp':<8} {'Completeness':<12} {'Validity':<10}")
    print("-" * 35)
    
    for temp, result in results.items():
        if "error" not in result:
            print(f"{temp:<8} {result['completeness']:<12.1f}% {result['validity']:<10.1f}%")
        else:
            print(f"{temp:<8} {'ERROR':<12} {'ERROR':<10}")


def main():
    """Main demonstration function"""
    
    print("🤖 Groq Synthetic Data Generation Demo")
    print("=" * 60)
    
    try:
        # Check if Groq is available
        from langchain_groq import ChatGroq
        
        # Show available models
        print("📋 Available Groq Models:")
        models = GroqConfig.list_models()
        for model_name, info in models.items():
            print(f"   - {model_name}: {info.get('description', 'N/A')}")
        
        # Test different models
        test_groq_models()
        
        # Show optimization techniques
        demo_groq_optimization()
        
        # Show temperature effects
        demo_groq_temperature_effects()
        
        print(f"\n🎉 Groq demonstration completed!")
        
        print(f"\n💡 Groq Advantages:")
        print(f"   - Ultra-fast inference (up to 10x faster than alternatives)")
        print(f"   - Cost-effective pricing")
        print(f"   - Multiple model options for different use cases")
        print(f"   - Large context windows")
        print(f"   - Reliable API with high uptime")
        
    except ImportError as e:
        print(f"⚠️ Note: Groq features require additional dependencies:")
        print(f"   pip install langchain-groq")
        print(f"   Set GROQ_API_KEY environment variable")
        print(f"   Error: {e}")
    except Exception as e:
        print(f"❌ Groq demonstration failed: {e}")
        print(f"💡 This might be due to missing API keys or network issues")


if __name__ == "__main__":
    main()
