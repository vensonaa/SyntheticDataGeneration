#!/usr/bin/env python3
"""
Demonstration of different LangGraph types for synthetic data generation
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import SchemaDefinition, FieldDefinition, DataType
from src.synthetic_data_generator import SyntheticDataGenerator


def create_simple_schema() -> SchemaDefinition:
    """Create a simple schema for testing"""
    
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
            name="is_active",
            data_type=DataType.BOOLEAN,
            required=True
        )
    ]
    
    return SchemaDefinition(
        name="test_data",
        description="Simple test data for graph type comparison",
        fields=fields,
        record_count=20
    )


def test_graph_type(graph_type: str, schema: SchemaDefinition) -> dict:
    """Test a specific graph type and return performance metrics"""
    
    print(f"\n🔄 Testing {graph_type.upper()} graph type...")
    
    # Create generator
    generator = SyntheticDataGenerator(graph_type=graph_type)
    
    # Measure generation time
    start_time = time.time()
    results = generator.generate_data(schema)
    end_time = time.time()
    
    generation_time = end_time - start_time
    
    if "error" in results:
        print(f"❌ {graph_type.upper()} generation failed: {results['error']}")
        return {
            "graph_type": graph_type,
            "success": False,
            "error": results["error"],
            "generation_time": generation_time
        }
    
    # Calculate metrics
    record_count = len(results["generated_records"])
    quality_metrics = results.get("quality_metrics", {})
    
    print(f"✅ {graph_type.upper()} completed:")
    print(f"   - Records generated: {record_count}")
    print(f"   - Generation time: {generation_time:.2f} seconds")
    print(f"   - Completeness: {quality_metrics.get('completeness', 0):.1f}%")
    print(f"   - Validity: {quality_metrics.get('validity', 0):.1f}%")
    
    return {
        "graph_type": graph_type,
        "success": True,
        "record_count": record_count,
        "generation_time": generation_time,
        "completeness": quality_metrics.get('completeness', 0),
        "validity": quality_metrics.get('validity', 0)
    }


def main():
    """Main function to demonstrate different graph types"""
    
    print("🚀 LangGraph Types Demonstration")
    print("=" * 50)
    
    # Create test schema
    schema = create_simple_schema()
    
    # Test different graph types
    graph_types = ["standard", "parallel", "adaptive"]
    results = []
    
    for graph_type in graph_types:
        result = test_graph_type(graph_type, schema)
        results.append(result)
    
    # Summary comparison
    print(f"\n📊 Graph Types Comparison Summary")
    print("=" * 50)
    
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        print(f"{'Graph Type':<12} {'Records':<8} {'Time (s)':<10} {'Completeness':<12} {'Validity':<10}")
        print("-" * 60)
        
        for result in successful_results:
            print(f"{result['graph_type']:<12} {result['record_count']:<8} {result['generation_time']:<10.2f} {result['completeness']:<12.1f}% {result['validity']:<10.1f}%")
        
        # Find fastest and highest quality
        fastest = min(successful_results, key=lambda x: x["generation_time"])
        highest_quality = max(successful_results, key=lambda x: x["completeness"] + x["validity"])
        
        print(f"\n🏆 Performance Summary:")
        print(f"   - Fastest: {fastest['graph_type']} ({fastest['generation_time']:.2f}s)")
        print(f"   - Highest Quality: {highest_quality['graph_type']} ({highest_quality['completeness']:.1f}% + {highest_quality['validity']:.1f}%)")
    
    # Show failed results
    failed_results = [r for r in results if not r["success"]]
    if failed_results:
        print(f"\n❌ Failed Graph Types:")
        for result in failed_results:
            print(f"   - {result['graph_type']}: {result['error']}")
    
    print(f"\n💡 Graph Type Recommendations:")
    print(f"   - STANDARD: Best for small datasets and simple validation")
    print(f"   - PARALLEL: Best for large datasets and performance")
    print(f"   - ADAPTIVE: Best for complex data with quality requirements")
    
    print(f"\n🎉 Demonstration completed!")


if __name__ == "__main__":
    main()
