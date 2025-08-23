from typing import Dict, List, Any, Optional
import json
import pandas as pd
from datetime import datetime
from .models import GenerationState, SchemaDefinition, GeneratedRecord
from .graph_nodes import create_synthetic_data_graph, create_parallel_generation_graph, create_adaptive_generation_graph
from .validators import QualityMetrics


class SyntheticDataGenerator:
    """Main class for generating synthetic data using LangGraph"""
    
    def __init__(self, graph_type: str = "standard"):
        """
        Initialize the synthetic data generator
        
        Args:
            graph_type: Type of graph to use ("standard", "parallel", "adaptive")
        """
        self.graph_type = graph_type
        self.graph = self._create_graph()
        self.app = self.graph.compile()
    
    def _create_graph(self):
        """Create the appropriate graph based on type"""
        if self.graph_type == "parallel":
            return create_parallel_generation_graph()
        elif self.graph_type == "adaptive":
            return create_adaptive_generation_graph()
        else:
            return create_synthetic_data_graph()
    
    def generate_data(self, schema: SchemaDefinition, **kwargs) -> Dict[str, Any]:
        """
        Generate synthetic data based on the provided schema
        
        Args:
            schema: Schema definition for the data to generate
            **kwargs: Additional parameters for generation
            
        Returns:
            Dictionary containing generated data and metadata
        """
        # Create initial state
        initial_state = GenerationState(
            schema=schema,
            context=kwargs
        )
        
        # Run the graph
        try:
            final_state = self.app.invoke(initial_state, config={"recursion_limit": 200})
            
            # Handle different state types
            if hasattr(final_state, 'generated_records'):
                generated_records = final_state.generated_records
                quality_metrics = final_state.generation_stats
                validation_errors = final_state.validation_errors
            else:
                # Handle AddableValuesDict case
                generated_records = final_state.get('generated_records', [])
                quality_metrics = final_state.get('generation_stats', {})
                validation_errors = final_state.get('validation_errors', [])
            
            # Extract results
            results = {
                "generated_records": [record.dict() if hasattr(record, 'dict') else record for record in generated_records],
                "quality_metrics": quality_metrics,
                "validation_errors": validation_errors,
                "generation_metadata": {
                    "schema_name": schema.name,
                    "record_count": len(generated_records),
                    "graph_type": self.graph_type,
                    "generation_timestamp": datetime.now().isoformat()
                }
            }
            
            return results
            
        except Exception as e:
            return {
                "error": str(e),
                "generated_records": [],
                "quality_metrics": {},
                "validation_errors": [str(e)]
            }
    
    def generate_dataframe(self, schema: SchemaDefinition, **kwargs) -> pd.DataFrame:
        """
        Generate synthetic data and return as a pandas DataFrame
        
        Args:
            schema: Schema definition for the data to generate
            **kwargs: Additional parameters for generation
            
        Returns:
            Pandas DataFrame with generated data
        """
        results = self.generate_data(schema, **kwargs)
        
        if "error" in results:
            raise ValueError(f"Generation failed: {results['error']}")
        
        # Convert to DataFrame
        records = results["generated_records"]
        if not records:
            return pd.DataFrame()
        
        # Extract data from records
        data_list = [record["data"] for record in records]
        df = pd.DataFrame(data_list)
        
        return df
    
    def generate_json(self, schema: SchemaDefinition, **kwargs) -> str:
        """
        Generate synthetic data and return as JSON string
        
        Args:
            schema: Schema definition for the data to generate
            **kwargs: Additional parameters for generation
            
        Returns:
            JSON string with generated data
        """
        results = self.generate_data(schema, **kwargs)
        return json.dumps(results, indent=2, default=str)
    
    def generate_csv(self, schema: SchemaDefinition, output_path: str, **kwargs) -> str:
        """
        Generate synthetic data and save to CSV file
        
        Args:
            schema: Schema definition for the data to generate
            output_path: Path to save the CSV file
            **kwargs: Additional parameters for generation
            
        Returns:
            Path to the generated CSV file
        """
        df = self.generate_dataframe(schema, **kwargs)
        df.to_csv(output_path, index=False)
        return output_path
    
    def validate_schema(self, schema: SchemaDefinition) -> Dict[str, Any]:
        """
        Validate a schema definition
        
        Args:
            schema: Schema definition to validate
            
        Returns:
            Validation results
        """
        errors = []
        warnings = []
        
        # Check if schema has fields
        if not schema.fields:
            errors.append("Schema must have at least one field")
        
        # Validate each field
        field_names = set()
        for field in schema.fields:
            # Check for duplicate field names
            if field.name in field_names:
                errors.append(f"Duplicate field name: {field.name}")
            field_names.add(field.name)
            
            # Validate field constraints
            if field.min_length and field.max_length and field.min_length > field.max_length:
                errors.append(f"Field '{field.name}': min_length cannot be greater than max_length")
            
            if field.min_value and field.max_value and field.min_value > field.max_value:
                errors.append(f"Field '{field.name}': min_value cannot be greater than max_value")
            
            # Check data type compatibility
            if field.data_type.value in ["integer", "float"] and field.choices:
                for choice in field.choices:
                    if not isinstance(choice, (int, float)):
                        warnings.append(f"Field '{field.name}': choice '{choice}' is not compatible with data type {field.data_type.value}")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }
    
    def get_quality_report(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a detailed quality report for generated data
        
        Args:
            results: Results from generate_data method
            
        Returns:
            Detailed quality report
        """
        if "error" in results:
            return {"error": results["error"]}
        
        records = [GeneratedRecord(**record) for record in results["generated_records"]]
        
        # Calculate additional metrics
        quality_metrics = results.get("quality_metrics", {})
        
        # Add data distribution analysis
        if records:
            df = pd.DataFrame([record.data for record in records])
            distribution_analysis = {}
            
            for column in df.columns:
                if df[column].dtype in ['int64', 'float64']:
                    distribution_analysis[column] = {
                        "mean": float(df[column].mean()),
                        "std": float(df[column].std()),
                        "min": float(df[column].min()),
                        "max": float(df[column].max())
                    }
                elif df[column].dtype == 'object':
                    value_counts = df[column].value_counts()
                    distribution_analysis[column] = {
                        "unique_values": int(value_counts.nunique()),
                        "most_common": value_counts.head(3).to_dict()
                    }
            
            quality_metrics["distribution_analysis"] = distribution_analysis
        
        return quality_metrics
    
    def set_graph_type(self, graph_type: str):
        """
        Change the graph type and recompile
        
        Args:
            graph_type: New graph type ("standard", "parallel", "adaptive")
        """
        self.graph_type = graph_type
        self.graph = self._create_graph()
        self.app = self.graph.compile()
    
    def get_graph_info(self) -> Dict[str, Any]:
        """
        Get information about the current graph
        
        Returns:
            Graph information
        """
        return {
            "graph_type": self.graph_type,
            "nodes": list(self.graph.nodes.keys()),
            "edges": str(self.graph.edges)
        }
