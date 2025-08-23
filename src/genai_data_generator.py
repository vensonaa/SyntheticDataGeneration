"""
GenAI-enhanced synthetic data generator
"""

from typing import Dict, List, Any, Optional
import json
import pandas as pd
from datetime import datetime
from .models import GenerationState, SchemaDefinition, GeneratedRecord
from .genai_nodes import create_genai_enhanced_graph
from .llm_generators import register_llm_generators
from .validators import QualityMetrics
from .env_config import EnvConfig
from .groq_config import GroqConfig


class GenAISyntheticDataGenerator:
    """GenAI-enhanced synthetic data generator using LLM capabilities"""
    
    def __init__(self, model_name: str = None):
        """
        Initialize the GenAI-enhanced data generator with Groq
        
        Args:
            model_name: Groq model to use (uses env default if None)
        """
        # Load environment configuration
        EnvConfig.load_env()
        
        # Use environment default if not specified
        if model_name is None:
            model_name = EnvConfig.get_default_model()
        
        self.llm_provider = "groq"
        self.model_name = model_name
        self.graph = create_genai_enhanced_graph()
        self.app = self.graph.compile()
        
        # Register LLM generators
        register_llm_generators()
    
    def generate_data(self, schema: SchemaDefinition, **kwargs) -> Dict[str, Any]:
        """
        Generate synthetic data using GenAI capabilities
        
        Args:
            schema: Schema definition for the data to generate
            **kwargs: Additional parameters for generation
            
        Returns:
            Dictionary containing generated data and metadata
        """
        # Enhanced context with GenAI parameters
        enhanced_context = {
            **kwargs,
            "llm_provider": self.llm_provider,
            "model_name": self.model_name,
            "generation_mode": "genai_enhanced",
            "use_contextual_generation": kwargs.get("use_contextual_generation", EnvConfig.is_contextual_generation_enabled()),
            "quality_enhancement": kwargs.get("quality_enhancement", EnvConfig.is_quality_enhancement_enabled()),
            "adaptive_strategy": kwargs.get("adaptive_strategy", True)
        }
        
        # Create initial state
        initial_state = GenerationState(
            schema=schema,
            context=enhanced_context
        )
        
        # Run the GenAI-enhanced graph
        try:
            final_state = self.app.invoke(initial_state, config={"recursion_limit": EnvConfig.get_recursion_limit()})
            
            # Handle different state types
            if hasattr(final_state, 'generated_records'):
                generated_records = final_state.generated_records
                quality_metrics = final_state.generation_stats
                validation_errors = final_state.validation_errors
                context = final_state.context
            else:
                # Handle AddableValuesDict case
                generated_records = final_state.get('generated_records', [])
                quality_metrics = final_state.get('generation_stats', {})
                validation_errors = final_state.get('validation_errors', [])
                context = final_state.get('context', {})
            
            # Extract results with GenAI metadata
            results = {
                "generated_records": [record.dict() if hasattr(record, 'dict') else record for record in generated_records],
                "quality_metrics": quality_metrics,
                "validation_errors": validation_errors,
                "generation_metadata": {
                    "schema_name": schema.name,
                    "record_count": len(generated_records),
                    "generation_method": "genai_enhanced",
                    "llm_provider": self.llm_provider,
                    "model_name": self.model_name,
                    "generation_timestamp": datetime.now().isoformat(),
                    "llm_adaptations": context.get("adaptation_count", 0),
                    "quality_enhancements": sum(1 for record in generated_records 
                                              if isinstance(record, dict) and record.get("generation_metadata", {}).get("llm_enhanced", False))
                }
            }
            
            return results
            
        except Exception as e:
            return {
                "error": str(e),
                "generated_records": [],
                "quality_metrics": {},
                "validation_errors": [str(e)],
                "generation_metadata": {
                    "schema_name": schema.name,
                    "generation_method": "genai_enhanced",
                    "error": True
                }
            }
    
    def generate_with_personas(self, schema: SchemaDefinition, personas: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        Generate data with specific personas/archetypes
        
        Args:
            schema: Schema definition
            personas: List of persona definitions
            **kwargs: Additional parameters
            
        Returns:
            Generated data with persona-based characteristics
        """
        all_records = []
        all_metadata = []
        
        records_per_persona = schema.record_count // len(personas)
        
        for i, persona in enumerate(personas):
            # Create schema for this persona
            persona_schema = SchemaDefinition(
                name=f"{schema.name}_persona_{i}",
                description=f"{schema.description} - {persona.get('name', 'Persona')}",
                fields=schema.fields,
                record_count=records_per_persona,
                relationships=schema.relationships,
                constraints=schema.constraints
            )
            
            # Enhanced context with persona
            persona_context = {
                **kwargs,
                "persona": persona,
                "persona_characteristics": persona.get("characteristics", {}),
                "persona_preferences": persona.get("preferences", {}),
                "persona_demographics": persona.get("demographics", {})
            }
            
            # Generate data for this persona
            persona_results = self.generate_data(persona_schema, **persona_context)
            
            if "error" not in persona_results:
                # Tag records with persona information
                for record in persona_results["generated_records"]:
                    if isinstance(record, dict) and "generation_metadata" in record:
                        record["generation_metadata"]["persona"] = persona
                    elif isinstance(record, dict):
                        record["persona_info"] = persona.get("name", f"Persona_{i}")
                
                all_records.extend(persona_results["generated_records"])
                all_metadata.append(persona_results["generation_metadata"])
        
        # Combine results
        combined_results = {
            "generated_records": all_records,
            "quality_metrics": self._combine_quality_metrics([r.get("quality_metrics", {}) for r in [{"quality_metrics": {}}] * len(all_metadata)]),
            "validation_errors": [],
            "generation_metadata": {
                "schema_name": schema.name,
                "record_count": len(all_records),
                "generation_method": "genai_enhanced_personas",
                "personas_used": len(personas),
                "persona_metadata": all_metadata,
                "generation_timestamp": datetime.now().isoformat()
            }
        }
        
        return combined_results
    
    def generate_with_relationships(self, schemas: List[SchemaDefinition], relationships: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Generate related datasets with maintained relationships
        
        Args:
            schemas: List of schema definitions
            relationships: Relationship definitions between schemas
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with generated data for all schemas with maintained relationships
        """
        results = {}
        
        # Generate data in dependency order
        for schema in schemas:
            # Check if this schema depends on others
            dependencies = relationships.get(schema.name, {}).get("depends_on", [])
            
            # Build context with related data
            related_context = {**kwargs}
            for dep in dependencies:
                if dep in results:
                    related_context[f"{dep}_data"] = results[dep]["generated_records"]
            
            # Generate data for this schema
            schema_results = self.generate_data(schema, **related_context)
            results[schema.name] = schema_results
        
        return results
    
    def _combine_quality_metrics(self, metrics_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine quality metrics from multiple generations"""
        if not metrics_list or not any(metrics_list):
            return {}
        
        # Calculate averages for numeric metrics
        combined = {}
        numeric_fields = ["completeness", "validity", "total_records"]
        
        for field in numeric_fields:
            values = [m.get(field, 0) for m in metrics_list if m and field in m]
            if values:
                combined[field] = sum(values) / len(values) if field != "total_records" else sum(values)
        
        return combined
    
    def generate_dataframe(self, schema: SchemaDefinition, **kwargs) -> pd.DataFrame:
        """Generate synthetic data and return as pandas DataFrame"""
        results = self.generate_data(schema, **kwargs)
        
        if "error" in results:
            raise ValueError(f"Generation failed: {results['error']}")
        
        # Convert to DataFrame
        records = results["generated_records"]
        if not records:
            return pd.DataFrame()
        
        # Extract data from records
        data_list = []
        for record in records:
            if isinstance(record, dict):
                if "data" in record:
                    data_list.append(record["data"])
                else:
                    # Remove metadata fields for clean DataFrame
                    clean_record = {k: v for k, v in record.items() 
                                  if k not in ["generation_metadata", "validation_errors", "is_valid"]}
                    data_list.append(clean_record)
        
        df = pd.DataFrame(data_list)
        return df
    
    def get_generation_insights(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Get insights about the GenAI generation process"""
        metadata = results.get("generation_metadata", {})
        
        insights = {
            "generation_method": metadata.get("generation_method", "unknown"),
            "llm_provider": metadata.get("llm_provider", "unknown"),
            "model_used": metadata.get("model_name", "unknown"),
            "total_records": metadata.get("record_count", 0),
            "llm_adaptations": metadata.get("llm_adaptations", 0),
            "quality_enhancements": metadata.get("quality_enhancements", 0),
            "enhancement_rate": 0
        }
        
        if insights["total_records"] > 0:
            insights["enhancement_rate"] = (insights["quality_enhancements"] / insights["total_records"]) * 100
        
        return insights
