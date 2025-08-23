from typing import Dict, List, Any, Optional
from .models import FieldDefinition, GeneratedRecord, DataType
import re
from datetime import datetime


class DataValidator:
    """Base class for data validation"""
    
    def validate(self, field_def: FieldDefinition, value: Any) -> List[str]:
        """Validate a single field value and return list of errors"""
        errors = []
        
        # Check if required field is present
        if field_def.required and value is None:
            errors.append(f"Field '{field_def.name}' is required but value is None")
            return errors
        
        # Skip validation if value is None and field is not required
        if value is None:
            return errors
        
        # Type-specific validation
        errors.extend(self._validate_type(field_def, value))
        
        # Constraint validation
        errors.extend(self._validate_constraints(field_def, value))
        
        return errors
    
    def _validate_type(self, field_def: FieldDefinition, value: Any) -> List[str]:
        """Validate data type"""
        errors = []
        
        if field_def.data_type == DataType.STRING:
            if not isinstance(value, str):
                errors.append(f"Field '{field_def.name}' must be a string, got {type(value)}")
        
        elif field_def.data_type == DataType.INTEGER:
            if not isinstance(value, int):
                errors.append(f"Field '{field_def.name}' must be an integer, got {type(value)}")
        
        elif field_def.data_type == DataType.FLOAT:
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field_def.name}' must be a number, got {type(value)}")
        
        elif field_def.data_type == DataType.BOOLEAN:
            if not isinstance(value, bool):
                errors.append(f"Field '{field_def.name}' must be a boolean, got {type(value)}")
        
        elif field_def.data_type == DataType.DATE:
            if not isinstance(value, str):
                errors.append(f"Field '{field_def.name}' must be a date string, got {type(value)}")
            else:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    errors.append(f"Field '{field_def.name}' must be a valid ISO date format")
        
        elif field_def.data_type == DataType.DATETIME:
            if not isinstance(value, str):
                errors.append(f"Field '{field_def.name}' must be a datetime string, got {type(value)}")
            else:
                try:
                    datetime.fromisoformat(value)
                except ValueError:
                    errors.append(f"Field '{field_def.name}' must be a valid ISO datetime format")
        
        elif field_def.data_type == DataType.EMAIL:
            if not isinstance(value, str):
                errors.append(f"Field '{field_def.name}' must be a string, got {type(value)}")
            else:
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, value):
                    errors.append(f"Field '{field_def.name}' must be a valid email address")
        
        return errors
    
    def _validate_constraints(self, field_def: FieldDefinition, value: Any) -> List[str]:
        """Validate field constraints"""
        errors = []
        
        # Length constraints for strings
        if field_def.data_type == DataType.STRING and isinstance(value, str):
            if field_def.min_length and len(value) < field_def.min_length:
                errors.append(f"Field '{field_def.name}' must be at least {field_def.min_length} characters")
            
            if field_def.max_length and len(value) > field_def.max_length:
                errors.append(f"Field '{field_def.name}' must be at most {field_def.max_length} characters")
        
        # Value range constraints for numbers
        if field_def.data_type in [DataType.INTEGER, DataType.FLOAT]:
            if field_def.min_value is not None and value < field_def.min_value:
                errors.append(f"Field '{field_def.name}' must be at least {field_def.min_value}")
            
            if field_def.max_value is not None and value > field_def.max_value:
                errors.append(f"Field '{field_def.name}' must be at most {field_def.max_value}")
        
        # Pattern validation for strings
        if field_def.pattern and isinstance(value, str):
            if not re.match(field_def.pattern, value):
                errors.append(f"Field '{field_def.name}' must match pattern: {field_def.pattern}")
        
        # Choice validation
        if field_def.choices and value not in field_def.choices:
            errors.append(f"Field '{field_def.name}' must be one of: {field_def.choices}")
        
        return errors


class RecordValidator:
    """Validator for complete records"""
    
    def __init__(self):
        self.field_validator = DataValidator()
    
    def validate_record(self, record: GeneratedRecord, schema_fields: List[FieldDefinition]) -> GeneratedRecord:
        """Validate a complete record against schema"""
        errors = []
        
        # Validate each field
        for field_def in schema_fields:
            value = record.data.get(field_def.name)
            field_errors = self.field_validator.validate(field_def, value)
            errors.extend(field_errors)
        
        # Check for missing required fields
        for field_def in schema_fields:
            if field_def.required and field_def.name not in record.data:
                errors.append(f"Required field '{field_def.name}' is missing")
        
        # Update record validation status
        record.validation_errors = errors
        record.is_valid = len(errors) == 0
        
        return record
    
    def validate_relationships(self, record: GeneratedRecord, relationships: Dict[str, Any]) -> List[str]:
        """Validate record relationships"""
        errors = []
        
        if not relationships:
            return errors
        
        # Example: Foreign key validation
        for rel_name, rel_config in relationships.items():
            if rel_name in record.data:
                # Add relationship validation logic here
                pass
        
        return errors


class QualityMetrics:
    """Calculate quality metrics for generated data"""
    
    @staticmethod
    def calculate_completeness(records: List[GeneratedRecord], schema_fields: List[FieldDefinition]) -> float:
        """Calculate completeness percentage"""
        if not records:
            return 0.0
        
        total_fields = len(schema_fields) * len(records)
        filled_fields = 0
        
        for record in records:
            for field_def in schema_fields:
                if field_def.name in record.data and record.data[field_def.name] is not None:
                    filled_fields += 1
        
        return (filled_fields / total_fields) * 100 if total_fields > 0 else 0.0
    
    @staticmethod
    def calculate_validity(records: List[GeneratedRecord]) -> float:
        """Calculate validity percentage"""
        if not records:
            return 0.0
        
        valid_records = sum(1 for record in records if record.is_valid)
        return (valid_records / len(records)) * 100
    
    @staticmethod
    def calculate_uniqueness(records: List[GeneratedRecord], unique_fields: List[str]) -> Dict[str, float]:
        """Calculate uniqueness percentage for specified fields"""
        if not records or not unique_fields:
            return {}
        
        uniqueness_scores = {}
        
        for field_name in unique_fields:
            values = [record.data.get(field_name) for record in records if record.data.get(field_name) is not None]
            unique_values = set(values)
            uniqueness_scores[field_name] = (len(unique_values) / len(values)) * 100 if values else 0.0
        
        return uniqueness_scores
    
    @staticmethod
    def generate_quality_report(records: List[GeneratedRecord], schema_fields: List[FieldDefinition]) -> Dict[str, Any]:
        """Generate comprehensive quality report"""
        return {
            "total_records": len(records),
            "completeness": QualityMetrics.calculate_completeness(records, schema_fields),
            "validity": QualityMetrics.calculate_validity(records),
            "field_statistics": QualityMetrics._calculate_field_statistics(records, schema_fields),
            "validation_errors": QualityMetrics._summarize_validation_errors(records)
        }
    
    @staticmethod
    def _calculate_field_statistics(records: List[GeneratedRecord], schema_fields: List[FieldDefinition]) -> Dict[str, Any]:
        """Calculate statistics for each field"""
        stats = {}
        
        for field_def in schema_fields:
            field_name = field_def.name
            values = [record.data.get(field_name) for record in records if record.data.get(field_name) is not None]
            
            stats[field_name] = {
                "filled_count": len(values),
                "null_count": len(records) - len(values),
                "unique_count": len(set(values)) if values else 0,
                "data_type": field_def.data_type.value
            }
        
        return stats
    
    @staticmethod
    def _summarize_validation_errors(records: List[GeneratedRecord]) -> Dict[str, int]:
        """Summarize validation errors by type"""
        error_counts = {}
        
        for record in records:
            for error in record.validation_errors:
                error_type = error.split(":")[0] if ":" in error else "Unknown"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return error_counts
