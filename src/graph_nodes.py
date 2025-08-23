from typing import Dict, Any, List
from langgraph.graph import StateGraph, END
from .models import GenerationState, GeneratedRecord, FieldDefinition
from .generators import GeneratorFactory
from .validators import RecordValidator, QualityMetrics


def initialize_generators(state: GenerationState) -> GenerationState:
    """Initialize field generators for the schema"""
    field_generators = {}
    
    for field_def in state.data_schema.fields:
        generator = GeneratorFactory.get_generator(field_def.data_type)
        field_generators[field_def.name] = generator
    
    # Create new state with field generators
    new_state = GenerationState(
        schema=state.data_schema,
        generated_records=state.generated_records,
        current_record=state.current_record,
        field_generators=field_generators,
        validation_errors=state.validation_errors,
        generation_stats=state.generation_stats,
        context=state.context
    )
    return new_state


def generate_single_record(state: GenerationState) -> GenerationState:
    """Generate a single record with all fields"""
    record_data = {}
    
    for field_def in state.data_schema.fields:
        generator = state.field_generators[field_def.name]
        
        # Generate value for the field
        value = generator.generate(field_def, state.context)
        
        # Apply default value if generation failed and default is specified
        if value is None and field_def.default_value is not None:
            value = field_def.default_value
        
        record_data[field_def.name] = value
    
    # Create generated record
    generated_record = GeneratedRecord(
        data=record_data,
        generation_metadata={
            "generation_timestamp": "2024-01-01T00:00:00Z",  # You can use actual timestamp
            "schema_name": state.data_schema.name
        }
    )
    
    # Create a new state with updated records
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


def validate_record(state: GenerationState) -> GenerationState:
    """Validate the current record"""
    if not state.generated_records:
        return state
    
    validator = RecordValidator()
    current_record = state.generated_records[-1]
    
    # Validate the record
    validated_record = validator.validate_record(
        current_record, 
        state.data_schema.fields
    )
    
    # Create new records list with validated record
    updated_records = state.generated_records[:-1] + [validated_record]
    
    # Create new state
    new_state = GenerationState(
        schema=state.data_schema,
        generated_records=updated_records,
        current_record=state.current_record,
        field_generators=state.field_generators,
        validation_errors=state.validation_errors + (validated_record.validation_errors if not validated_record.is_valid else []),
        generation_stats=state.generation_stats,
        context=state.context
    )
    
    return new_state


def should_continue_generation(state: GenerationState) -> str:
    """Determine if we should continue generating records"""
    current_count = len(state.generated_records)
    target_count = state.data_schema.record_count
    
    # Safety check to prevent infinite loops
    if current_count >= target_count:
        return "end"
    
    # Additional safety check
    if current_count > 1000:  # Emergency stop
        return "end"
    
    return "continue"


def calculate_quality_metrics(state: GenerationState) -> GenerationState:
    """Calculate quality metrics for all generated records"""
    if not state.generated_records:
        return state
    
    quality_report = QualityMetrics.generate_quality_report(
        state.generated_records,
        state.data_schema.fields
    )
    
    # Create new state with updated stats
    new_state = GenerationState(
        schema=state.data_schema,
        generated_records=state.generated_records,
        current_record=state.current_record,
        field_generators=state.field_generators,
        validation_errors=state.validation_errors,
        generation_stats=quality_report,
        context=state.context
    )
    return new_state


def handle_generation_error(state: GenerationState) -> GenerationState:
    """Handle generation errors and retry logic"""
    # Add error handling logic here
    # For now, just log the error and continue
    return state


def create_synthetic_data_graph() -> StateGraph:
    """Create the LangGraph for synthetic data generation"""
    
    # Create the graph
    workflow = StateGraph(GenerationState)
    
    # Add nodes
    workflow.add_node("initialize_generators", initialize_generators)
    workflow.add_node("generate_record", generate_single_record)
    workflow.add_node("validate_record", validate_record)
    workflow.add_node("calculate_metrics", calculate_quality_metrics)
    
    # Add conditional edge
    workflow.add_conditional_edges(
        "validate_record",
        should_continue_generation,
        {
            "continue": "generate_record",
            "end": "calculate_metrics"
        }
    )
    
    # Add edges
    workflow.add_edge("initialize_generators", "generate_record")
    workflow.add_edge("generate_record", "validate_record")
    workflow.add_edge("calculate_metrics", END)
    
    # Set entry point
    workflow.set_entry_point("initialize_generators")
    
    return workflow


def create_parallel_generation_graph() -> StateGraph:
    """Create a graph that can generate multiple records in parallel"""
    
    workflow = StateGraph(GenerationState)
    
    # Add nodes
    workflow.add_node("initialize_generators", initialize_generators)
    workflow.add_node("generate_batch", generate_record_batch)
    workflow.add_node("validate_batch", validate_record_batch)
    workflow.add_node("calculate_metrics", calculate_quality_metrics)
    
    # Add conditional edge
    workflow.add_conditional_edges(
        "validate_batch",
        should_continue_generation,
        {
            "continue": "generate_batch",
            "end": "calculate_metrics"
        }
    )
    
    # Add edges
    workflow.add_edge("initialize_generators", "generate_batch")
    workflow.add_edge("generate_batch", "validate_batch")
    workflow.add_edge("calculate_metrics", END)
    
    # Set entry point
    workflow.set_entry_point("initialize_generators")
    
    return workflow


def generate_record_batch(state: GenerationState) -> GenerationState:
    """Generate multiple records in a batch"""
    batch_size = min(10, state.data_schema.record_count - len(state.generated_records))
    
    for _ in range(batch_size):
        state = generate_single_record(state)
    
    return state


def validate_record_batch(state: GenerationState) -> GenerationState:
    """Validate multiple records in a batch"""
    if not state.generated_records:
        return state
    
    validator = RecordValidator()
    
    # Validate all records in the batch
    for i, record in enumerate(state.generated_records):
        validated_record = validator.validate_record(record, state.data_schema.fields)
        state.generated_records[i] = validated_record
        
        if not validated_record.is_valid:
            state.validation_errors.extend(validated_record.validation_errors)
    
    return state


def create_adaptive_generation_graph() -> StateGraph:
    """Create a graph that adapts generation based on quality metrics"""
    
    workflow = StateGraph(GenerationState)
    
    # Add nodes
    workflow.add_node("initialize_generators", initialize_generators)
    workflow.add_node("generate_record", generate_single_record)
    workflow.add_node("validate_record", validate_record)
    workflow.add_node("adapt_generation", adapt_generation_strategy)
    workflow.add_node("calculate_metrics", calculate_quality_metrics)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "validate_record",
        should_continue_generation,
        {
            "continue": "adapt_generation",
            "end": "calculate_metrics"
        }
    )
    
    workflow.add_edge("adapt_generation", "generate_record")
    
    # Add edges
    workflow.add_edge("initialize_generators", "generate_record")
    workflow.add_edge("generate_record", "validate_record")
    workflow.add_edge("calculate_metrics", END)
    
    # Set entry point
    workflow.set_entry_point("initialize_generators")
    
    return workflow


def adapt_generation_strategy(state: GenerationState) -> GenerationState:
    """Adapt generation strategy based on current quality metrics"""
    if len(state.generated_records) < 10:
        return state  # Not enough data to adapt yet
    
    # Calculate current quality
    recent_records = state.generated_records[-10:]
    validity_rate = QualityMetrics.calculate_validity(recent_records)
    
    # Adapt generation strategy based on quality
    if validity_rate < 80:
        # Low quality - adjust generation parameters
        state.context["quality_issue"] = True
        state.context["retry_count"] = state.context.get("retry_count", 0) + 1
    else:
        # Good quality - continue normally
        state.context["quality_issue"] = False
    
    return state
