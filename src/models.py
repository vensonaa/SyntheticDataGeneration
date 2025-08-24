from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from enum import Enum



class DataType(str, Enum):
    """Supported data types for synthetic data generation"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    ADDRESS = "address"
    NAME = "name"
    CUSTOM = "custom"


class FieldDefinition(BaseModel):
    """Definition of a single field in the data schema"""
    name: str
    data_type: DataType
    required: bool = True
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    pattern: Optional[str] = None
    choices: Optional[List[Any]] = None
    default_value: Optional[Any] = None
    custom_generator: Optional[str] = None
    dependencies: Optional[Dict[str, Any]] = None


class SchemaDefinition(BaseModel):
    """Complete schema definition for synthetic data generation"""
    name: str
    description: Optional[str] = None
    fields: List[FieldDefinition]
    relationships: Optional[Dict[str, Any]] = None
    constraints: Optional[Dict[str, Any]] = None
    record_count: int = 100


class GeneratedRecord(BaseModel):
    """A single generated record with validation status"""
    data: Dict[str, Any]
    is_valid: bool = True
    validation_errors: List[str] = Field(default_factory=list)
    generation_metadata: Dict[str, Any] = Field(default_factory=dict)


class GenerationState(BaseModel):
    """State object passed between LangGraph nodes"""
    data_schema: SchemaDefinition = Field(alias="schema")
    generated_records: List[GeneratedRecord] = Field(default_factory=list)
    current_record: Optional[Dict[str, Any]] = None
    field_generators: Dict[str, Any] = Field(default_factory=dict)
    validation_errors: List[str] = Field(default_factory=list)
    generation_stats: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        populate_by_name = True



