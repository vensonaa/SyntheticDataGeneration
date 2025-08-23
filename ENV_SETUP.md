# Environment Configuration Setup

## Overview

This guide explains how to set up and use environment configuration for the synthetic data generation system using `.env` files.

## 🚀 Quick Start

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Edit Your Configuration

Open `.env` and update with your actual values:

```env
# Groq API Configuration
GROQ_API_KEY=your_actual_groq_api_key_here

# Generation Settings
DEFAULT_RECORD_COUNT=1000
DEFAULT_BATCH_SIZE=10

# Model Configuration
DEFAULT_GROQ_MODEL=llama3-8b-8192
DEFAULT_TEMPERATURE=0.5

# Quality Settings
ENABLE_QUALITY_ENHANCEMENT=true
ENABLE_CONTEXTUAL_GENERATION=true

# Performance Settings
RECURSION_LIMIT=200
MAX_RETRIES=3

# Output Settings
DEFAULT_OUTPUT_FORMAT=json
ENABLE_CSV_EXPORT=true
```

### 3. Test Configuration

```bash
python examples/env_config_example.py
```

## 📋 Configuration Options

### Groq API Configuration

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Your Groq API key | - | ✅ Yes |

**How to get your API key:**
1. Visit [Groq Console](https://console.groq.com)
2. Sign up for a free account
3. Navigate to API Keys section
4. Generate a new API key
5. Copy and paste into your `.env` file

### Generation Settings

| Variable | Description | Default | Type |
|----------|-------------|---------|------|
| `DEFAULT_RECORD_COUNT` | Default number of records to generate | 1000 | Integer |
| `DEFAULT_BATCH_SIZE` | Default batch size for processing | 10 | Integer |

### Model Configuration

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `DEFAULT_GROQ_MODEL` | Default Groq model to use | llama3-8b-8192 | llama3-8b-8192, llama3-70b-8192, mixtral-8x7b-32768, gemma2-9b-it |
| `DEFAULT_TEMPERATURE` | Default temperature for generation | 0.5 | 0.0-1.0 |

### Quality Settings

| Variable | Description | Default | Type |
|----------|-------------|---------|------|
| `ENABLE_QUALITY_ENHANCEMENT` | Enable automatic quality improvement | true | Boolean |
| `ENABLE_CONTEXTUAL_GENERATION` | Enable contextual data generation | true | Boolean |

### Performance Settings

| Variable | Description | Default | Type |
|----------|-------------|---------|------|
| `RECURSION_LIMIT` | Maximum recursion depth for LangGraph | 200 | Integer |
| `MAX_RETRIES` | Maximum retry attempts for failed operations | 3 | Integer |

### Output Settings

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `DEFAULT_OUTPUT_FORMAT` | Default output format | json | json, csv, dataframe |
| `ENABLE_CSV_EXPORT` | Enable CSV export functionality | true | Boolean |

## 🔧 Usage Examples

### Basic Usage

```python
from src.env_config import EnvConfig
from src.genai_data_generator import GenAISyntheticDataGenerator

# Load environment configuration
EnvConfig.load_env()

# Create generator (uses environment defaults)
generator = GenAISyntheticDataGenerator()

# Generate data
results = generator.generate_data(schema)
```

### Override Environment Settings

```python
# Override model
generator = GenAISyntheticDataGenerator(model_name="llama3-70b-8192")

# Override temperature
results = generator.generate_data(schema, temperature=0.8)

# Override quality settings
results = generator.generate_data(
    schema,
    use_contextual_generation=False,
    quality_enhancement=False
)
```

### Check Configuration

```python
from src.env_config import EnvConfig

# Print current configuration
EnvConfig.print_config()

# Get specific values
model = EnvConfig.get_default_model()
temperature = EnvConfig.get_default_temperature()
api_key = EnvConfig.get_groq_api_key()
```

## 🛠️ Environment Management

### Multiple Environments

You can have different `.env` files for different environments:

```bash
# Development
cp .env.example .env.dev

# Production
cp .env.example .env.prod

# Testing
cp .env.example .env.test
```

### Load Specific Environment

```python
from src.env_config import EnvConfig

# Load specific environment file
EnvConfig.load_env(".env.prod")
```

### Environment Variables Override

Environment variables take precedence over `.env` file values:

```bash
# Override API key via environment variable
export GROQ_API_KEY="different_api_key"

# Override model
export DEFAULT_GROQ_MODEL="llama3-70b-8192"
```

## 🔒 Security Best Practices

### 1. Never Commit `.env` Files

Add `.env` to your `.gitignore`:

```gitignore
# Environment files
.env
.env.local
.env.prod
.env.staging
```

### 2. Use `.env.example` for Documentation

Keep `.env.example` updated with all available options (without real values):

```env
# Example configuration - copy to .env and update values
GROQ_API_KEY=your_api_key_here
DEFAULT_GROQ_MODEL=llama3-8b-8192
```

### 3. Validate Configuration

```python
from src.env_config import setup_environment

# Validate and get configuration status
config = setup_environment()

if not config['groq_api_key']:
    print("Warning: API key not configured")
```

## 🚨 Troubleshooting

### Common Issues

1. **API Key Not Found**
   ```
   Error: Groq API key not found. Please set GROQ_API_KEY in your .env file
   ```
   **Solution**: Add your API key to the `.env` file

2. **Invalid Model Name**
   ```
   Error: Unknown model: invalid-model
   ```
   **Solution**: Use one of the supported models: `llama3-8b-8192`, `llama3-70b-8192`, `mixtral-8x7b-32768`, `gemma2-9b-it`

3. **Configuration Not Loading**
   ```
   Error: .env file not found
   ```
   **Solution**: Ensure `.env` file exists in the project root

4. **Invalid Boolean Values**
   ```
   Error: Invalid boolean value
   ```
   **Solution**: Use `true`/`false` (lowercase) for boolean values

### Debug Configuration

```python
from src.env_config import EnvConfig

# Print detailed configuration
EnvConfig.print_config()

# Check specific values
print(f"API Key: {'Set' if EnvConfig.get_groq_api_key() else 'Not set'}")
print(f"Model: {EnvConfig.get_default_model()}")
print(f"Temperature: {EnvConfig.get_default_temperature()}")
```

## 📊 Configuration Validation

The system automatically validates your configuration:

```python
from src.env_config import EnvConfig

# Validate configuration
config = EnvConfig.validate_config()

print(f"API Key: {'✅' if config['groq_api_key'] else '❌'}")
print(f"Model: {config['default_model']}")
print(f"Quality Enhancement: {'✅' if config['quality_enhancement'] else '❌'}")
```

## 🔄 Migration from Hardcoded Values

If you have existing code with hardcoded values, here's how to migrate:

### Before (Hardcoded)
```python
generator = GenAISyntheticDataGenerator(model_name="llama3-8b-8192")
results = generator.generate_data(schema, temperature=0.5)
```

### After (Environment-based)
```python
# .env file
DEFAULT_GROQ_MODEL=llama3-8b-8192
DEFAULT_TEMPERATURE=0.5

# Code
generator = GenAISyntheticDataGenerator()  # Uses env defaults
results = generator.generate_data(schema)   # Uses env defaults
```

## 📈 Performance Optimization

### Recommended Settings by Use Case

**High-Volume Generation:**
```env
DEFAULT_GROQ_MODEL=llama3-8b-8192
DEFAULT_TEMPERATURE=0.3
RECURSION_LIMIT=500
```

**Quality-Critical Applications:**
```env
DEFAULT_GROQ_MODEL=llama3-70b-8192
DEFAULT_TEMPERATURE=0.5
ENABLE_QUALITY_ENHANCEMENT=true
```

**Development/Testing:**
```env
DEFAULT_RECORD_COUNT=10
DEFAULT_GROQ_MODEL=llama3-8b-8192
DEFAULT_TEMPERATURE=0.7
```

## 🎯 Next Steps

1. **Set up your `.env` file** with your Groq API key
2. **Test the configuration** with `python examples/env_config_example.py`
3. **Run the full demo** with `python examples/groq_example.py`
4. **Customize settings** based on your use case
5. **Deploy with confidence** using environment-specific configurations

---

This environment configuration system provides a secure, flexible, and maintainable way to manage your synthetic data generation settings across different environments and use cases.
