from typing import Dict, List, Any, Optional
import json
import pandas as pd
from datetime import datetime
from .models import GenerationState, SchemaDefinition, GeneratedRecord
from .graph_nodes import create_synthetic_data_graph, create_parallel_generation_graph, create_adaptive_generation_graph
from .validators import QualityMetrics
from .sqlite_storage import get_storage_manager


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
                - recursion_limit: Maximum recursion limit (default: 1000)
            
        Returns:
            Dictionary containing generated data and metadata
        """
        # Create initial state
        initial_state = GenerationState(
            schema=schema,
            context=kwargs
        )
        
        # Get recursion limit from kwargs or use default
        recursion_limit = kwargs.get('recursion_limit', 1000)
        
        # Run the graph
        try:
            final_state = self.app.invoke(initial_state, config={"recursion_limit": recursion_limit})
            
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
    
    def generate_to_sqlite(self, schema: SchemaDefinition, table_name: str = None, 
                          db_path: str = None, **kwargs) -> Dict[str, Any]:
        """
        Generate synthetic data and store in SQLite database
        
        Args:
            schema: Schema definition for the data to generate
            table_name: Name of the table to create/use (defaults to schema name)
            db_path: Path to SQLite database file
            **kwargs: Additional parameters for generation
            
        Returns:
            Dictionary with generation and storage results
        """
        # Generate data
        results = self.generate_data(schema, **kwargs)
        
        if "error" in results:
            return results
        
        # Determine table name
        if table_name is None:
            table_name = schema.name.lower().replace(' ', '_').replace('-', '_')
        
        # Get storage manager
        storage_manager = get_storage_manager(db_path)
        
        # Store data in SQLite
        storage_result = storage_manager.insert_data(
            table_name=table_name,
            data=results.get('generated_records', []),
            schema_definition=schema.dict()
        )
        
        # Combine results
        combined_results = {
            **results,
            'storage_result': storage_result,
            'table_name': table_name,
            'database_path': storage_manager.db_path
        }
        
        return combined_results
    
    def generate_with_storage_options(self, schema: SchemaDefinition, 
                                    storage_options: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Generate synthetic data with flexible storage options
        
        Args:
            schema: Schema definition for the data to generate
            storage_options: Dictionary with storage configuration
                - save_to_sqlite: bool (default True)
                - save_to_csv: bool (default False)
                - table_name: str (optional)
                - db_path: str (optional)
                - csv_path: str (optional)
            **kwargs: Additional parameters for generation
            
        Returns:
            Dictionary with generation and storage results
        """
        if storage_options is None:
            storage_options = {}
        
        # Default storage options
        save_to_sqlite = storage_options.get('save_to_sqlite', True)
        save_to_csv = storage_options.get('save_to_csv', False)
        table_name = storage_options.get('table_name')
        db_path = storage_options.get('db_path')
        csv_path = storage_options.get('csv_path')
        
        # Generate data
        results = self.generate_data(schema, **kwargs)
        
        if "error" in results:
            return results
        
        storage_results = {}
        
        # Store in SQLite if requested
        if save_to_sqlite:
            if table_name is None:
                table_name = schema.name.lower().replace(' ', '_').replace('-', '_')
            
            storage_manager = get_storage_manager(db_path)
            sqlite_result = storage_manager.insert_data(
                table_name=table_name,
                data=results.get('generated_records', []),
                schema_definition=schema.dict()
            )
            storage_results['sqlite'] = sqlite_result
        
        # Save to CSV if requested
        if save_to_csv:
            if csv_path is None:
                csv_path = f"{schema.name.lower().replace(' ', '_')}.csv"
            
            df = pd.DataFrame([record['data'] for record in results.get('generated_records', [])])
            df.to_csv(csv_path, index=False)
            storage_results['csv'] = {
                'success': True,
                'file_path': csv_path,
                'record_count': len(df)
            }
        
        # Combine results
        combined_results = {
            **results,
            'storage_results': storage_results,
            'storage_options_used': storage_options
        }
        
        return combined_results
    
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
