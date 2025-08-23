#!/usr/bin/env python3
"""
Demo: Groq Configuration and Setup (No API Key Required)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.groq_config import GroqConfig, GroqOptimizer


def demo_groq_configuration():
    """Demonstrate Groq configuration without API calls"""
    
    print("🤖 Groq Configuration Demo")
    print("=" * 50)
    
    # Show available models
    print("📋 Available Groq Models:")
    models = GroqConfig.list_models()
    for model_name, info in models.items():
        print(f"   - {model_name}")
        print(f"     Description: {info.get('description', 'N/A')}")
        print(f"     Max Tokens: {info.get('max_tokens', 'N/A')}")
        print(f"     Best For: {info.get('best_for', 'N/A')}")
        print()
    
    # Show temperature presets
    print("🌡️ Temperature Presets:")
    for preset, temp in GroqConfig.TEMPERATURE_PRESETS.items():
        print(f"   - {preset.capitalize()}: {temp}")
    
    # Model recommendations
    print(f"\n🎯 Model Recommendations:")
    use_cases = ["speed", "quality", "context", "structured"]
    for use_case in use_cases:
        recommended = GroqConfig.recommend_model(use_case)
        model_info = GroqConfig.get_model_info(recommended)
        print(f"   {use_case.capitalize()}: {recommended} - {model_info.get('description', 'N/A')}")


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
    
    print(f"\nOriginal prompt preview:")
    print(f"'{original_prompt[:100]}...'")
    
    print(f"\nOptimized prompt preview:")
    print(f"'{optimized_prompt[:100]}...'")
    
    # Test chunking
    large_text = "This is a very long text. " * 1000  # Create a large text
    chunks = GroqOptimizer.chunk_large_inputs(large_text, max_tokens=1000)
    
    print(f"\n📦 Text Chunking:")
    print(f"Original text: {GroqOptimizer.estimate_tokens(large_text)} tokens")
    print(f"Chunked into: {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"   Chunk {i+1}: {GroqOptimizer.estimate_tokens(chunk)} tokens")


def demo_synthetic_data_integration():
    """Show how Groq integrates with synthetic data generation"""
    
    print(f"\n🔗 Synthetic Data Integration")
    print("=" * 50)
    
    print("The Groq integration provides several benefits for synthetic data generation:")
    print()
    
    benefits = [
        {
            "feature": "Contextual Generation",
            "description": "Generate data that makes logical sense together",
            "example": "If a person is a 'Doctor', their bio and skills will be medically relevant"
        },
        {
            "feature": "Realistic Relationships", 
            "description": "Fields that relate to each other naturally",
            "example": "Age, profession, and income levels that correlate realistically"
        },
        {
            "feature": "Quality Enhancement",
            "description": "Self-improving quality based on patterns and feedback",
            "example": "LLM identifies and fixes inconsistencies automatically"
        },
        {
            "feature": "Fast Inference",
            "description": "Ultra-fast generation with Groq's optimized infrastructure",
            "example": "Up to 10x faster than traditional LLM providers"
        },
        {
            "feature": "Cost Effective",
            "description": "Lower costs compared to other LLM providers",
            "example": "Pay only for what you use with transparent pricing"
        }
    ]
    
    for i, benefit in enumerate(benefits, 1):
        print(f"{i}. {benefit['feature']}")
        print(f"   {benefit['description']}")
        print(f"   Example: {benefit['example']}")
        print()


def demo_usage_examples():
    """Show usage examples for different scenarios"""
    
    print(f"\n💡 Usage Examples")
    print("=" * 50)
    
    examples = [
        {
            "scenario": "Fast Data Generation",
            "model": "llama3-8b-8192",
            "temperature": "0.3",
            "use_case": "High-volume synthetic data generation"
        },
        {
            "scenario": "High Quality Data",
            "model": "llama3-70b-8192", 
            "temperature": "0.5",
            "use_case": "Complex data with realistic relationships"
        },
        {
            "scenario": "Large Context Processing",
            "model": "mixtral-8x7b-32768",
            "temperature": "0.4",
            "use_case": "Complex schemas with many relationships"
        },
        {
            "scenario": "Structured Data",
            "model": "gemma2-9b-it",
            "temperature": "0.2",
            "use_case": "Formatted data following specific patterns"
        }
    ]
    
    for example in examples:
        print(f"📋 {example['scenario']}")
        print(f"   Model: {example['model']}")
        print(f"   Temperature: {example['temperature']}")
        print(f"   Use Case: {example['use_case']}")
        print()


def main():
    """Main demonstration function"""
    
    print("🚀 Groq Synthetic Data Generation - Configuration Demo")
    print("=" * 70)
    print("This demo shows Groq configuration and optimization techniques")
    print("without requiring an API key.")
    print()
    
    try:
        # Demo Groq configuration
        demo_groq_configuration()
        
        # Demo optimization techniques
        demo_groq_optimization()
        
        # Demo integration benefits
        demo_synthetic_data_integration()
        
        # Demo usage examples
        demo_usage_examples()
        
        print(f"\n🎉 Configuration demo completed!")
        
        print(f"\n📋 Next Steps:")
        print(f"   1. Get a Groq API key from https://console.groq.com")
        print(f"   2. Set environment variable: export GROQ_API_KEY='your-key'")
        print(f"   3. Run: python examples/groq_example.py")
        print(f"   4. Or run: python examples/genai_example.py")
        
        print(f"\n💡 Groq Advantages for Synthetic Data:")
        print(f"   ✅ Ultra-fast inference (up to 10x faster)")
        print(f"   ✅ Cost-effective pricing")
        print(f"   ✅ Multiple model options")
        print(f"   ✅ Large context windows")
        print(f"   ✅ Reliable API with high uptime")
        print(f"   ✅ No rate limits on most models")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


if __name__ == "__main__":
    main()
