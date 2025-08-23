"""
GenAI-enhanced LangGraph nodes for intelligent synthetic data generation
"""

from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
import json
from .models import GenerationState, GeneratedRecord, FieldDefinition
from .llm_generators import LLMContextualGenerator
from .validators import RecordValidator, QualityMetrics

# Import ChatGroq only when needed to avoid compatibility issues
def get_chat_groq():
    try:
        from langchain_groq import ChatGroq
        return ChatGroq
    except ImportError:
        raise ImportError("langchain-groq is not installed. Run: pip install langchain-groq")


def llm_generate_contextual_record(state: GenerationState) -> GenerationState:
    """Generate a complete record using LLM with full contextual awareness"""
    
    # Initialize LLM generator
    llm_generator = LLMContextualGenerator()
    
    # Generate contextually aware record
    try:
        record_data = llm_generator.generate_complete_record(
            state.data_schema.fields,
            state.context
        )
        
        # Ensure all required fields are present
        for field_def in state.data_schema.fields:
            if field_def.required and field_def.name not in record_data:
                # Fallback to individual generation
                from .generators import GeneratorFactory
                generator = GeneratorFactory.get_generator(field_def.data_type)
                record_data[field_def.name] = generator.generate(field_def, state.context)
        
        # Create generated record
        generated_record = GeneratedRecord(
            data=record_data,
            generation_metadata={
                "generation_method": "llm_contextual",
                "generation_timestamp": "2024-01-01T00:00:00Z",
                "schema_name": state.data_schema.name
            }
        )
        
        # Create new state with updated records
        new_state = GenerationState(
            schema=state.data_schema,
            generated_records=state.generated_records + [generated_record],
            current_record=record_data,
            field_generators=state.field_generators,
            validation_errors=state.validation_errors,
            generation_stats=state.generation_stats,
            context=state.context
        )
        
        return new_state
        
    except Exception as e:
        # Fallback to standard generation
        print(f"LLM generation failed, falling back to standard: {e}")
        from .graph_nodes import generate_single_record
        return generate_single_record(state)


def llm_enhance_data_quality(state: GenerationState) -> GenerationState:
    """Use LLM to enhance data quality and fix inconsistencies"""
    
    if not state.generated_records:
        return state
    
    ChatGroq = get_chat_groq()
    llm = ChatGroq(
        groq_api_key=None,  # Will use environment variable
        model_name="llama3-8b-8192",
        temperature=0.3  # Lower temperature for consistency
    )
    
    # Get the last generated record
    last_record = state.generated_records[-1]
    
    if not last_record.is_valid or last_record.validation_errors:
        # Use LLM to fix validation errors
        prompt = PromptTemplate(
            input_variables=["record_data", "errors", "schema"],
            template="""Fix the following data record to resolve validation errors:
            
            Record: {record_data}
            Validation Errors: {errors}
            Schema Requirements: {schema}
            
            Requirements:
            - Fix all validation errors
            - Maintain data realism
            - Return valid JSON
            - Keep existing valid data unchanged
            
            Fixed JSON:"""
        )
        
        schema_info = []
        for field in state.data_schema.fields:
            constraints = []
            if field.required:
                constraints.append("required")
            if field.min_value is not None:
                constraints.append(f"min: {field.min_value}")
            if field.max_value is not None:
                constraints.append(f"max: {field.max_value}")
            if field.choices:
                constraints.append(f"choices: {field.choices}")
            
            constraint_str = f" ({', '.join(constraints)})" if constraints else ""
            schema_info.append(f"{field.name}: {field.data_type.value}{constraint_str}")
        
        try:
            result = llm(prompt.format(
                record_data=json.dumps(last_record.data),
                errors=", ".join(last_record.validation_errors),
                schema="; ".join(schema_info)
            ))
            
            # Parse the fixed data
            import re
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                fixed_data = json.loads(json_match.group())
                
                # Create updated record
                updated_record = GeneratedRecord(
                    data=fixed_data,
                    generation_metadata={
                        **last_record.generation_metadata,
                        "llm_enhanced": True,
                        "original_errors": last_record.validation_errors
                    }
                )
                
                # Validate the fixed record
                validator = RecordValidator()
                validated_record = validator.validate_record(updated_record, state.data_schema.fields)
                
                # Update state with fixed record
                updated_records = state.generated_records[:-1] + [validated_record]
                
                new_state = GenerationState(
                    schema=state.data_schema,
                    generated_records=updated_records,
                    current_record=state.current_record,
                    field_generators=state.field_generators,
                    validation_errors=state.validation_errors,
                    generation_stats=state.generation_stats,
                    context=state.context
                )
                
                return new_state
                
        except Exception as e:
            print(f"LLM enhancement failed: {e}")
    
    return state


def llm_adaptive_strategy(state: GenerationState) -> GenerationState:
    """Use LLM to adapt generation strategy based on quality analysis"""
    
    if len(state.generated_records) < 10:
        return state  # Not enough data for analysis
    
    # Analyze recent generation quality
    recent_records = state.generated_records[-10:]
    quality_metrics = QualityMetrics.generate_quality_report(recent_records, state.data_schema.fields)
    
    ChatGroq = get_chat_groq()
    llm = ChatGroq(
        groq_api_key=None,  # Will use environment variable
        model_name="llama3-8b-8192",
        temperature=0.5
    )
    
    prompt = PromptTemplate(
        input_variables=["quality_metrics", "schema", "context"],
        template="""Analyze the following data generation quality metrics and suggest improvements:
        
        Quality Metrics: {quality_metrics}
        Schema: {schema}
        Current Context: {context}
        
        Based on this analysis, suggest specific improvements for:
        1. Field generation strategies
        2. Validation approaches
        3. Context enhancements
        4. Quality targets
        
        Return your suggestions as JSON with keys: field_strategies, validation_improvements, context_updates, quality_targets
        
        Suggestions:"""
    )
    
    schema_summary = f"Fields: {[f.name for f in state.data_schema.fields]}, Record count target: {state.data_schema.record_count}"
    
    try:
        result = llm(prompt.format(
            quality_metrics=json.dumps(quality_metrics),
            schema=schema_summary,
            context=json.dumps(state.context)
        ))
        
        # Parse suggestions
        import re
        json_match = re.search(r'\{.*\}', result, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
            
            # Update context with suggestions
            updated_context = {
                **state.context,
                "llm_suggestions": suggestions,
                "adaptation_count": state.context.get("adaptation_count", 0) + 1,
                "quality_trend": "improving" if quality_metrics.get("validity", 0) > 90 else "needs_improvement"
            }
            
            new_state = GenerationState(
                schema=state.data_schema,
                generated_records=state.generated_records,
                current_record=state.current_record,
                field_generators=state.field_generators,
                validation_errors=state.validation_errors,
                generation_stats=state.generation_stats,
                context=updated_context
            )
            
            return new_state
            
    except Exception as e:
        print(f"LLM adaptation failed: {e}")
    
    return state


def create_genai_enhanced_graph():
    """Create a LangGraph with GenAI-enhanced nodes"""
    from langgraph.graph import StateGraph, END
    from .models import GenerationState
    from .graph_nodes import initialize_generators, validate_record, calculate_quality_metrics, should_continue_generation
    
    # Create the graph
    workflow = StateGraph(GenerationState)
    
    # Add nodes (mix of standard and GenAI-enhanced)
    workflow.add_node("initialize_generators", initialize_generators)
    workflow.add_node("generate_record", llm_generate_contextual_record)  # GenAI-enhanced
    workflow.add_node("validate_record", validate_record)
    workflow.add_node("enhance_quality", llm_enhance_data_quality)  # GenAI-enhanced
    workflow.add_node("adapt_strategy", llm_adaptive_strategy)  # GenAI-enhanced
    workflow.add_node("calculate_metrics", calculate_quality_metrics)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "enhance_quality",
        should_continue_generation,
        {
            "continue": "adapt_strategy",
            "end": "calculate_metrics"
        }
    )
    
    # Add edges
    workflow.add_edge("initialize_generators", "generate_record")
    workflow.add_edge("generate_record", "validate_record")
    workflow.add_edge("validate_record", "enhance_quality")
    workflow.add_edge("adapt_strategy", "generate_record")
    workflow.add_edge("calculate_metrics", END)
    
    # Set entry point
    workflow.set_entry_point("initialize_generators")
    
    return workflow
