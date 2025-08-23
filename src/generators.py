from typing import Any, Dict, List, Optional
from faker import Faker
import random
import re
from datetime import datetime, timedelta
from .models import DataType, FieldDefinition

fake = Faker()


class FieldGenerator:
    """Base class for field generators"""
    
    def __init__(self):
        self.fake = fake
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> Any:
        """Generate a value for the given field definition"""
        raise NotImplementedError


class StringGenerator(FieldGenerator):
    """Generator for string fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        min_len = field_def.min_length or 5
        max_len = field_def.max_length or 20
        
        if field_def.pattern:
            # Generate string matching regex pattern
            return self._generate_from_pattern(field_def.pattern, min_len, max_len)
        
        return fake.text(max_nb_chars=max_len)[:max_len]


class IntegerGenerator(FieldGenerator):
    """Generator for integer fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> int:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        min_val = field_def.min_value or 0
        max_val = field_def.max_value or 1000
        
        return random.randint(min_val, max_val)


class FloatGenerator(FieldGenerator):
    """Generator for float fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> float:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        min_val = field_def.min_value or 0.0
        max_val = field_def.max_value or 1000.0
        
        return round(random.uniform(min_val, max_val), 2)


class BooleanGenerator(FieldGenerator):
    """Generator for boolean fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> bool:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        return random.choice([True, False])


class DateGenerator(FieldGenerator):
    """Generator for date fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        start_date = field_def.min_value or datetime.now() - timedelta(days=365)
        end_date = field_def.max_value or datetime.now()
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        random_date = fake.date_between(start_date=start_date, end_date=end_date)
        return random_date.isoformat()


class DateTimeGenerator(FieldGenerator):
    """Generator for datetime fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        start_date = field_def.min_value or datetime.now() - timedelta(days=365)
        end_date = field_def.max_value or datetime.now()
        
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        random_datetime = fake.date_time_between(start_date=start_date, end_date=end_date)
        return random_datetime.isoformat()


class EmailGenerator(FieldGenerator):
    """Generator for email fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        return fake.email()


class PhoneGenerator(FieldGenerator):
    """Generator for phone number fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        return fake.phone_number()


class AddressGenerator(FieldGenerator):
    """Generator for address fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        return fake.address()


class NameGenerator(FieldGenerator):
    """Generator for name fields"""
    
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> str:
        if field_def.choices:
            return random.choice(field_def.choices)
        
        return fake.name()


class GeneratorFactory:
    """Factory for creating field generators based on data type"""
    
    _generators = {
        DataType.STRING: StringGenerator(),
        DataType.INTEGER: IntegerGenerator(),
        DataType.FLOAT: FloatGenerator(),
        DataType.BOOLEAN: BooleanGenerator(),
        DataType.DATE: DateGenerator(),
        DataType.DATETIME: DateTimeGenerator(),
        DataType.EMAIL: EmailGenerator(),
        DataType.PHONE: PhoneGenerator(),
        DataType.ADDRESS: AddressGenerator(),
        DataType.NAME: NameGenerator(),
    }
    
    @classmethod
    def get_generator(cls, data_type: DataType) -> FieldGenerator:
        """Get the appropriate generator for the data type"""
        if data_type == DataType.CUSTOM:
            raise ValueError("Custom generators must be implemented separately")
        
        return cls._generators.get(data_type, StringGenerator())
    
    @classmethod
    def register_custom_generator(cls, data_type: DataType, generator: FieldGenerator):
        """Register a custom generator for a data type"""
        cls._generators[data_type] = generator
