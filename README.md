# Synthetic Data Generation with LangGraph

A powerful, scalable solution for generating synthetic test data using LangGraph, featuring configurable schemas, quality validation, and multiple generation strategies.

## 🏗️ Architecture Overview

This solution implements a LangGraph-based workflow for synthetic data generation with the following key components:

### Core Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Schema Parser │───▶│ Field Generator │───▶│ Data Validator  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  State Manager  │    │ Quality Metrics │    │ Output Formatter│
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### LangGraph Workflow

1. **Initialize Generators**: Set up field generators based on schema
2. **Generate Records**: Create individual records with all fields
3. **Validate Data**: Ensure data meets quality standards
4. **Calculate Metrics**: Generate quality reports
5. **Adapt Strategy**: Adjust generation based on quality (adaptive mode)

### Key Features

- **Multiple Data Types**: String, Integer, Float, Boolean, Date, Email, Phone, Address, Name
- **Configurable Constraints**: Min/max values, patterns, choices, dependencies
- **Quality Assurance**: Built-in validation and error handling
- **Multiple Generation Strategies**: Standard, Parallel, Adaptive
- **Relationship Support**: Maintain referential integrity
- **Extensible Design**: Easy to add custom generators and validators

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from src.models import SchemaDefinition, FieldDefinition, DataType
from src.synthetic_data_generator import SyntheticDataGenerator

# Create a simple schema
schema = SchemaDefinition(
    name="user_data",
    fields=[
        FieldDefinition(name="id", data_type=DataType.INTEGER, required=True),
        FieldDefinition(name="name", data_type=DataType.NAME, required=True),
        FieldDefinition(name="email", data_type=DataType.EMAIL, required=True),
        FieldDefinition(name="age", data_type=DataType.INTEGER, min_value=18, max_value=100)
    ],
    record_count=100
)

# Generate data
generator = SyntheticDataGenerator()
results = generator.generate_data(schema)

# Get as DataFrame
df = generator.generate_dataframe(schema)
```

## 📋 Data Types & Constraints

### Supported Data Types

| Type | Description | Example |
|------|-------------|---------|
| `STRING` | General text | "Sample text" |
| `INTEGER` | Whole numbers | 42 |
| `FLOAT` | Decimal numbers | 3.14 |
| `BOOLEAN` | True/False values | True |
| `DATE` | Date strings (ISO format) | "2024-01-01" |
| `DATETIME` | DateTime strings (ISO format) | "2024-01-01T12:00:00" |
| `EMAIL` | Email addresses | "user@example.com" |
| `PHONE` | Phone numbers | "+1-555-123-4567" |
| `ADDRESS` | Full addresses | "123 Main St, City, State" |
| `NAME` | Person names | "John Doe" |

### Field Constraints

```python
FieldDefinition(
    name="age",
    data_type=DataType.INTEGER,
    required=True,
    min_value=18,           # Minimum value
    max_value=100,          # Maximum value
    choices=[18, 25, 30],   # Specific choices
    pattern=r"^\d{2}$",     # Regex pattern (for strings)
    default_value=25        # Default if generation fails
)
```

## 🔧 Generation Strategies

### 1. Standard Generation
Sequential generation with validation after each record.

```python
generator = SyntheticDataGenerator(graph_type="standard")
```

### 2. Parallel Generation
Batch generation for improved performance.

```python
generator = SyntheticDataGenerator(graph_type="parallel")
```

### 3. Adaptive Generation
Quality-aware generation that adapts based on validation results.

```python
generator = SyntheticDataGenerator(graph_type="adaptive")
```

## 📊 Quality Metrics

The system provides comprehensive quality metrics:

- **Completeness**: Percentage of fields with values
- **Validity**: Percentage of records passing validation
- **Uniqueness**: Percentage of unique values in specified fields
- **Distribution Analysis**: Statistical analysis of numeric fields
- **Field Statistics**: Detailed breakdown by field

```python
# Get quality report
quality_report = generator.get_quality_report(results)
print(f"Completeness: {quality_report['completeness']:.1f}%")
print(f"Validity: {quality_report['validity']:.1f}%")
```

## 🛒 Examples

### User Data Generation

```bash
python examples/user_data_example.py
```

Generates user profiles with:
- Personal information (name, email, phone)
- Demographics (age, address)
- Account details (registration date, subscription type)
- Business metrics (monthly spend)

### E-commerce Data Generation

```bash
python examples/ecommerce_data_example.py
```

Creates a complete e-commerce dataset with:
- Products (ID, name, category, price, stock)
- Customers (profile, segment, registration)
- Orders (customer reference, status, payment)
- Order Items (product reference, quantity, pricing)

## 🔌 Extending the System

### Custom Field Generators

```python
from src.generators import FieldGenerator, GeneratorFactory
from src.models import FieldDefinition

class CustomGenerator(FieldGenerator):
    def generate(self, field_def: FieldDefinition, context: Dict[str, Any] = None) -> Any:
        # Your custom generation logic
        return "custom_value"

# Register the generator
GeneratorFactory.register_custom_generator(DataType.CUSTOM, CustomGenerator())
```

### Custom Validators

```python
from src.validators import DataValidator

class CustomValidator(DataValidator):
    def _validate_custom_constraint(self, field_def: FieldDefinition, value: Any) -> List[str]:
        # Your custom validation logic
        return []
```

## 📁 Project Structure

```
SyntheticDataGeneration/
├── src/
│   ├── __init__.py
│   ├── models.py              # Pydantic models and data structures
│   ├── generators.py          # Field generators for different data types
│   ├── validators.py          # Data validation and quality metrics
│   ├── graph_nodes.py         # LangGraph node implementations
│   └── synthetic_data_generator.py  # Main generator class
├── examples/
│   ├── user_data_example.py   # User data generation example
│   └── ecommerce_data_example.py  # E-commerce data example
├── requirements.txt           # Python dependencies
└── README.md                 # This file
```

## 🧪 Testing

```bash
# Run examples to test the system
python examples/user_data_example.py
python examples/ecommerce_data_example.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file for configuration:

```env
# Optional: OpenAI API key for advanced features
OPENAI_API_KEY=your_api_key_here

# Generation settings
DEFAULT_RECORD_COUNT=1000
DEFAULT_BATCH_SIZE=10
```

## 📈 Performance Considerations

- **Parallel Generation**: Use for large datasets (>1000 records)
- **Batch Processing**: Adjust batch size based on memory constraints
- **Quality vs Speed**: Adaptive generation trades speed for quality
- **Memory Usage**: Large datasets may require streaming processing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the examples for usage patterns
2. Review the architecture documentation
3. Open an issue with detailed error information

---

**Built with LangGraph, Pydantic, and Faker** 🚀
