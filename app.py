#!/usr/bin/env python3
"""
Flask web application for synthetic data generation
"""

import os
import json
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import tempfile

# Import our synthetic data generation modules
from src.env_config import EnvConfig, setup_environment
from src.models import SchemaDefinition, FieldDefinition, DataType
from src.database import SchemaTemplate
from src.synthetic_data_generator import SyntheticDataGenerator
from src.groq_config import GroqConfig
from src.database import init_database, get_db_manager
from src.sqlite_storage import get_storage_manager
from src.sql_dialect_generator import SQLDialectGenerator, get_supported_dialects
from src.llm_sql_generator import LLMSQLGenerator, get_supported_dialects


app = Flask(__name__)
app.secret_key = 'synthetic_data_generation_secret_key'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load environment configuration
setup_environment()

# Initialize database
init_database(app)


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')

@app.route('/test-frontend')
def test_frontend():
    """Test frontend functionality"""
    return send_file('test_frontend_schema_edit.html')

@app.route('/test-js-loading')
def test_js_loading():
    """Test JavaScript loading"""
    return send_file('test_js_loading.html')

@app.route('/test-schema-admin')
def test_schema_admin():
    """Test Schema Admin functionality"""
    return send_file('test_schema_admin_simple.html')

@app.route('/test-save-schema')
def test_save_schema():
    """Test Save Schema functionality"""
    return send_file('test_save_schema_minimal.html')

@app.route('/schema-admin')
def schema_admin():
    """Schema Administration page"""
    return render_template('schema_admin.html')


@app.route('/api/config')
def get_config():
    """Get current configuration"""
    try:
        config = EnvConfig.validate_config()
        models = GroqConfig.list_models()
        dialects = get_supported_dialects()
        
        return jsonify({
            'success': True,
            'config': config,
            'models': models,
            'temperature_presets': GroqConfig.TEMPERATURE_PRESETS,
            'sql_dialects': dialects
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/generate', methods=['POST'])
def generate_data():
    """Generate synthetic data based on schema"""
    try:
        data = request.get_json()
        
        # Extract parameters
        schema_data = data.get('schema', {})
        generation_params = data.get('generation_params', {})
        
        # Check if this is a multi-table schema
        if 'tables' in schema_data and schema_data['tables']:
            # Multi-table schema
            return generate_multi_table_data(schema_data, generation_params)
        else:
            # Single table schema
            return generate_single_table_data(schema_data, generation_params)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def generate_single_table_data(schema_data, generation_params):
    """Generate data for single table schema"""
    try:
        # Create schema definition
        fields = []
        for field_data in schema_data.get('fields', []):
            # Convert uppercase data type to lowercase for enum
            data_type_str = field_data['data_type'].lower()
            try:
                data_type = DataType(data_type_str)
            except ValueError:
                # Handle case where data type doesn't match enum
                raise ValueError(f"Invalid data type: {field_data['data_type']}. Valid types are: {[dt.value for dt in DataType]}")
            
            field = FieldDefinition(
                name=field_data['name'],
                data_type=data_type,
                required=field_data.get('required', True),
                min_value=field_data.get('min_value'),
                max_value=field_data.get('max_value'),
                min_length=field_data.get('min_length'),
                max_length=field_data.get('max_length'),
                pattern=field_data.get('pattern'),
                choices=field_data.get('choices'),
                default_value=field_data.get('default_value'),
                description=field_data.get('description')
            )
            fields.append(field)
        
        schema = SchemaDefinition(
            name=schema_data.get('name', 'generated_data'),
            description=schema_data.get('description', ''),
            fields=fields,
            record_count=generation_params.get('record_count', 100)
        )
        
        # Create generator
        generator = SyntheticDataGenerator()
        
        # Get generation parameters
        recursion_limit = generation_params.get('recursion_limit', 1000)
        
        # Generate data
        results = generator.generate_data(schema, recursion_limit=recursion_limit)
        
        if isinstance(results, dict) and 'error' in results:
            return jsonify({
                'success': False,
                'error': results['error']
            })
        
        # Save to database if requested
        save_to_db = generation_params.get('save_to_database', True)
        save_to_sqlite = generation_params.get('save_to_sqlite', True)
        dataset_id = None
        sqlite_result = None
        
        if save_to_db:
            try:
                db_manager = get_db_manager()
                dataset_id = db_manager.save_dataset(
                    name=schema.name,
                    description=schema.description or '',
                    schema_definition=schema.dict(),
                    records=records_data,
                    generation_metadata=results.get('generation_metadata', {}),
            
                )
            except Exception as db_error:
                print(f"Warning: Failed to save to database: {db_error}")
        
        # Save to SQLite if requested
        if save_to_sqlite:
            try:
                storage_manager = get_storage_manager()
                table_name = generation_params.get('table_name', schema.name.lower().replace(' ', '_'))
                sqlite_result = storage_manager.insert_data(
                    table_name=table_name,
                    data=records_data,
                    schema_definition=schema.dict()
                )
            except Exception as sqlite_error:
                print(f"Warning: Failed to save to SQLite: {sqlite_error}")
        
        # Extract data from GeneratedRecord objects for single table
        generated_records = results.get('generated_records', [])
        records_data = []
        for record in generated_records:
            if isinstance(record, dict) and 'data' in record:
                records_data.append(record['data'])
            elif hasattr(record, 'data'):
                records_data.append(record.data)
            else:
                records_data.append(record)
        
        # Prepare response
        response_data = {
            'success': True,
            'generated_records': records_data,

            'generation_metadata': results.get('generation_metadata', {}),
            'total_records': len(records_data),
            'dataset_id': dataset_id,
            'sqlite_result': sqlite_result
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def generate_multi_table_data(schema_data, generation_params):
    """Generate data for multi-table schema"""
    try:
        # Create generator
        generator = SyntheticDataGenerator()
        
        # Get generation parameters
        recursion_limit = generation_params.get('recursion_limit', 1000)
        record_count = generation_params.get('record_count', 100)
        
        # Generate data for each table
        all_generated_records = {}
        total_records = 0

        all_generation_metadata = {}
        
        for table_def in schema_data['tables']:
            table_name = table_def.get('name', 'table')
            
            # Create schema definition for this table
            fields = []
            for field_data in table_def.get('fields', []):
                # Convert uppercase data type to lowercase for enum
                data_type_str = field_data['data_type'].lower()
                try:
                    data_type = DataType(data_type_str)
                except ValueError:
                    raise ValueError(f"Invalid data type: {field_data['data_type']}. Valid types are: {[dt.value for dt in DataType]}")
                
                field = FieldDefinition(
                    name=field_data['name'],
                    data_type=data_type,
                    required=field_data.get('required', True),
                    min_value=field_data.get('min_value'),
                    max_value=field_data.get('max_value'),
                    min_length=field_data.get('min_length'),
                    max_length=field_data.get('max_length'),
                    pattern=field_data.get('pattern'),
                    choices=field_data.get('choices'),
                    default_value=field_data.get('default_value'),
                    description=field_data.get('description')
                )
                fields.append(field)
            
            schema = SchemaDefinition(
                name=table_name,
                description=table_def.get('description', ''),
                fields=fields,
                record_count=record_count
            )
            
            # Generate data for this table
            results = generator.generate_data(schema, recursion_limit=recursion_limit)
            
            if isinstance(results, dict) and 'error' in results:
                return jsonify({
                    'success': False,
                    'error': f"Error generating data for table '{table_name}': {results['error']}"
                })
            
            # Store results - extract data from GeneratedRecord objects
            generated_records = results.get('generated_records', [])
            # Convert GeneratedRecord objects to plain data dictionaries
            records_data = []
            for record in generated_records:
                if isinstance(record, dict) and 'data' in record:
                    records_data.append(record['data'])
                elif hasattr(record, 'data'):
                    records_data.append(record.data)
                else:
                    records_data.append(record)
            
            all_generated_records[table_name] = records_data
            total_records += len(records_data)
            
            
            if 'generation_metadata' in results:
                all_generation_metadata[table_name] = results['generation_metadata']
        
        # Save to database if requested
        save_to_db = generation_params.get('save_to_database', True)
        save_to_sqlite = generation_params.get('save_to_sqlite', True)
        dataset_id = None
        sqlite_results = {}
        
        if save_to_db:
            try:
                db_manager = get_db_manager()
                # Save each table as a separate dataset
                for table_name, records in all_generated_records.items():
                    table_def = next((t for t in schema_data['tables'] if t['name'] == table_name), {})
                    dataset_id = db_manager.save_dataset(
                        name=f"{schema_data.get('name', 'multi_table')}_{table_name}",
                        description=f"{schema_data.get('description', '')} - {table_name}",
                        schema_definition=table_def,
                        records=records,  # records is already the correct format from our extraction
                        generation_metadata=all_generation_metadata.get(table_name, {}),
            
                    )
            except Exception as db_error:
                print(f"Warning: Failed to save to database: {db_error}")
        
        # Save to SQLite if requested
        if save_to_sqlite:
            try:
                storage_manager = get_storage_manager()
                for table_name, records in all_generated_records.items():
                    table_def = next((t for t in schema_data['tables'] if t['name'] == table_name), {})
                    sqlite_result = storage_manager.insert_data(
                        table_name=table_name.lower().replace(' ', '_'),
                        data=records,
                        schema_definition=table_def
                    )
                    sqlite_results[table_name] = sqlite_result
            except Exception as sqlite_error:
                print(f"Warning: Failed to save to SQLite: {sqlite_error}")
        
        # Prepare response
        response_data = {
            'success': True,
            'generated_records': all_generated_records,

            'generation_metadata': all_generation_metadata,
            'total_records': total_records,
            'dataset_id': dataset_id,
            'sqlite_results': sqlite_results
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """Export generated data as CSV"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records to export'
            })
        
        # Convert to DataFrame - handle both old format (record['data']) and new format (direct record)
        data_for_df = []
        for record in records:
            if isinstance(record, dict) and 'data' in record:
                data_for_df.append(record['data'])
            else:
                data_for_df.append(record)
        df = pd.DataFrame(data_for_df)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            tmp_filename = tmp_file.name
        
        return send_file(
            tmp_filename,
            as_attachment=True,
            download_name=f'synthetic_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/export/json', methods=['POST'])
def export_json():
    """Export generated data as JSON"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records to export'
            })
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
            json.dump(records, tmp_file, indent=2, default=str)
            tmp_filename = tmp_file.name
        
        return send_file(
            tmp_filename,
            as_attachment=True,
            download_name=f'synthetic_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json',
            mimetype='application/json'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# @app.route('/api/schema/templates')  # REMOVED - No longer using predefined templates
def get_schema_templates():
    """Get predefined schema templates and custom templates from database"""
    # Predefined templates
    predefined_templates = {
        'user_data': {
            'name': 'User Data',
            'description': 'Synthetic user profiles with personal information',
            'fields': [
                {'name': 'id', 'data_type': 'INTEGER', 'required': True, 'min_value': 1, 'max_value': 10000},
                {'name': 'first_name', 'data_type': 'NAME', 'required': True},
                {'name': 'last_name', 'data_type': 'NAME', 'required': True},
                {'name': 'email', 'data_type': 'EMAIL', 'required': True},
                {'name': 'age', 'data_type': 'INTEGER', 'required': True, 'min_value': 18, 'max_value': 80},
                {'name': 'phone', 'data_type': 'PHONE', 'required': False},
                {'name': 'address', 'data_type': 'ADDRESS', 'required': False},
                {'name': 'registration_date', 'data_type': 'DATE', 'required': True},
                {'name': 'is_active', 'data_type': 'BOOLEAN', 'required': True}
            ]
        },
        'ecommerce_products': {
            'name': 'E-commerce Products',
            'description': 'Product catalog with pricing and inventory',
            'fields': [
                {'name': 'product_id', 'data_type': 'INTEGER', 'required': True, 'min_value': 1, 'max_value': 10000},
                {'name': 'product_name', 'data_type': 'STRING', 'required': True, 'max_length': 100},
                {'name': 'category', 'data_type': 'STRING', 'required': True, 'choices': ['Electronics', 'Clothing', 'Books', 'Home', 'Sports']},
                {'name': 'price', 'data_type': 'FLOAT', 'required': True, 'min_value': 0.01, 'max_value': 10000},
                {'name': 'stock_quantity', 'data_type': 'INTEGER', 'required': True, 'min_value': 0, 'max_value': 1000},
                {'name': 'description', 'data_type': 'STRING', 'required': False, 'max_length': 500},
                {'name': 'created_date', 'data_type': 'DATE', 'required': True},
                {'name': 'is_featured', 'data_type': 'BOOLEAN', 'required': True}
            ]
        },
        'employee_data': {
            'name': 'Employee Data',
            'description': 'Employee records with professional information',
            'fields': [
                {'name': 'employee_id', 'data_type': 'INTEGER', 'required': True, 'min_value': 1, 'max_value': 10000},
                {'name': 'first_name', 'data_type': 'NAME', 'required': True},
                {'name': 'last_name', 'data_type': 'NAME', 'required': True},
                {'name': 'email', 'data_type': 'EMAIL', 'required': True},
                {'name': 'department', 'data_type': 'STRING', 'required': True, 'choices': ['Engineering', 'Marketing', 'Sales', 'HR', 'Finance', 'Operations']},
                {'name': 'position', 'data_type': 'STRING', 'required': True, 'max_length': 100},
                {'name': 'salary', 'data_type': 'FLOAT', 'required': True, 'min_value': 30000, 'max_value': 200000},
                {'name': 'hire_date', 'data_type': 'DATE', 'required': True},
                {'name': 'is_manager', 'data_type': 'BOOLEAN', 'required': True}
            ]
        },
        'healthcare_patients': {
            'name': 'Healthcare Patients',
            'description': 'Patient records with medical information',
            'fields': [
                {'name': 'patient_id', 'data_type': 'INTEGER', 'required': True, 'min_value': 1, 'max_value': 10000},
                {'name': 'first_name', 'data_type': 'NAME', 'required': True},
                {'name': 'last_name', 'data_type': 'NAME', 'required': True},
                {'name': 'date_of_birth', 'data_type': 'DATE', 'required': True},
                {'name': 'gender', 'data_type': 'STRING', 'required': True, 'choices': ['Male', 'Female', 'Other']},
                {'name': 'blood_type', 'data_type': 'STRING', 'required': False, 'choices': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']},
                {'name': 'phone', 'data_type': 'PHONE', 'required': True},
                {'name': 'emergency_contact', 'data_type': 'STRING', 'required': False, 'max_length': 100},
                {'name': 'has_insurance', 'data_type': 'BOOLEAN', 'required': True}
            ]
        }
    }
    
    # Get custom templates from database
    try:
        db_manager = get_db_manager()
        custom_templates = db_manager.get_schema_templates(limit=50)
        
        # Convert custom templates to the expected format
        for template in custom_templates:
            template_id = template['id']
            template_key = f"custom_{template_id}"
            
            # Handle multi-table schemas
            if template['schema_definition'].get('tables'):
                # For multi-table schemas, use the first table for the quick template
                first_table = template['schema_definition']['tables'][0]
                predefined_templates[template_key] = {
                    'name': f"{template['name']} ({first_table['display_name']})",
                    'description': f"{template['description']} - First table only",
                    'fields': first_table['fields']
                }
            else:
                # Single table schema
                predefined_templates[template_key] = {
                    'name': template['name'],
                    'description': template['description'],
                    'fields': template['schema_definition'].get('fields', [])
                }
    except Exception as e:
        print(f"Error loading custom templates: {e}")
        # Continue with predefined templates only
    
    return jsonify({
        'success': True,
        'templates': predefined_templates
    })


@app.route('/api/validate-schema', methods=['POST'])
def validate_schema():
    """Validate a schema definition"""
    try:
        data = request.get_json()
        schema_data = data.get('schema', {})
        
        # Create schema definition
        fields = []
        for field_data in schema_data.get('fields', []):
            # Convert uppercase data type to lowercase for enum
            data_type_str = field_data['data_type'].lower()
            try:
                data_type = DataType(data_type_str)
            except ValueError:
                # Handle case where data type doesn't match enum
                raise ValueError(f"Invalid data type: {field_data['data_type']}. Valid types are: {[dt.value for dt in DataType]}")
            
            field = FieldDefinition(
                name=field_data['name'],
                data_type=data_type,
                required=field_data.get('required', True),
                min_value=field_data.get('min_value'),
                max_value=field_data.get('max_value'),
                min_length=field_data.get('min_length'),
                max_length=field_data.get('max_length'),
                pattern=field_data.get('pattern'),
                choices=field_data.get('choices'),
                default_value=field_data.get('default_value'),
                description=field_data.get('description')
            )
            fields.append(field)
        
        schema = SchemaDefinition(
            name=schema_data.get('name', 'test_schema'),
            description=schema_data.get('description', ''),
            fields=fields,
            record_count=1
        )
        
        # Validate schema
        generator = SyntheticDataGenerator()
        validation = generator.validate_schema(schema)
        
        return jsonify({
            'success': True,
            'validation': validation
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# SQLite Database API Endpoints

@app.route('/api/datasets', methods=['GET', 'POST'])
def handle_datasets():
    """Handle datasets - GET for listing, POST for creating"""
    if request.method == 'GET':
        """Get list of saved datasets"""
        try:
            limit = request.args.get('limit', type=int, default=20)
            offset = request.args.get('offset', type=int, default=0)
            
            db_manager = get_db_manager()
            datasets = db_manager.get_datasets(limit=limit, offset=offset)
            
            return jsonify({
                'success': True,
                'datasets': datasets,
                'count': len(datasets)
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })
    
    elif request.method == 'POST':
        """Create a new dataset"""
        try:
            data = request.get_json()
            
            name = data.get('name')
            description = data.get('description', '')
            schema_definition = data.get('schema_definition', {})
            records = data.get('records', [])
            generation_metadata = data.get('generation_metadata', {})
    
            
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'Dataset name is required'
                }), 400
            
            if not records:
                return jsonify({
                    'success': False,
                    'error': 'No records to save'
                }), 400
            
            # Save to database
            
            db_manager = get_db_manager()
            dataset_id = db_manager.save_dataset(
                name=name,
                description=description,
                schema_definition=schema_definition,
                records=records,
                generation_metadata=generation_metadata,
    
            )
            
            return jsonify({
                'success': True,
                'message': f'Dataset "{name}" saved successfully',
                'dataset_id': dataset_id
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            })


@app.route('/api/datasets/<int:dataset_id>', methods=['GET'])
def get_dataset(dataset_id):
    """Get dataset details by ID"""
    try:
        db_manager = get_db_manager()
        dataset = db_manager.get_dataset(dataset_id)
        
        if dataset is None:
            return jsonify({
                'success': False,
                'error': 'Dataset not found'
            }), 404
        
        return jsonify({
            'success': True,
            'dataset': dataset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/datasets/<int:dataset_id>/records', methods=['GET'])
def get_dataset_records(dataset_id):
    """Get records for a dataset"""
    try:
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)
        
        db_manager = get_db_manager()
        records = db_manager.get_dataset_records(dataset_id, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'records': records,
            'count': len(records),
            'dataset_id': dataset_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/datasets/<int:dataset_id>/export/csv', methods=['GET'])
def export_dataset_csv(dataset_id):
    """Export dataset as CSV"""
    try:
        db_manager = get_db_manager()
        
        # Get dataset info
        dataset = db_manager.get_dataset(dataset_id)
        if dataset is None:
            return jsonify({
                'success': False,
                'error': 'Dataset not found'
            }), 404
        
        # Get all records
        records = db_manager.get_dataset_records(dataset_id, limit=None)
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records to export'
            })
        
        # Convert to DataFrame
        df = pd.DataFrame([record['record_data'] for record in records])
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            df.to_csv(tmp_file.name, index=False)
            tmp_filename = tmp_file.name
        
        return send_file(
            tmp_filename,
            as_attachment=True,
            download_name=f'{dataset["name"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
            mimetype='text/csv'
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/datasets/<int:dataset_id>/search', methods=['GET'])
def search_dataset_records(dataset_id):
    """Search records in a dataset"""
    try:
        query = request.args.get('q', '')
        limit = request.args.get('limit', type=int, default=100)
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Search query is required'
            })
        
        db_manager = get_db_manager()
        records = db_manager.search_records(dataset_id, query, limit=limit)
        
        return jsonify({
            'success': True,
            'records': records,
            'count': len(records),
            'query': query,
            'dataset_id': dataset_id
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/datasets/<int:dataset_id>', methods=['DELETE'])
def delete_dataset(dataset_id):
    """Delete a dataset and all its records"""
    try:
        db_manager = get_db_manager()
        deleted = db_manager.delete_dataset(dataset_id)
        
        if deleted:
            return jsonify({
                'success': True,
                'message': 'Dataset deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Dataset not found'
            }), 404
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })



    """Apply a saved dataset to a test database"""
    try:
        print(f"Applying dataset {dataset_id} to test database")
        data = request.get_json()
        test_db_name = data.get('test_db_name', f'dataset_{dataset_id}_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        
        print(f"Test database name: {test_db_name}")
        
        # Get the dataset
        db_manager = get_db_manager()
        dataset = db_manager.get_dataset(dataset_id)
        
        if not dataset:
            print(f"Dataset {dataset_id} not found")
            return jsonify({
                'success': False,
                'error': 'Dataset not found'
            }), 404
        
        print(f"Found dataset: {dataset['name']}")
        
        # Get dataset records
        records = db_manager.get_dataset_records(dataset_id, limit=10000)  # Get all records
        
        if not records:
            print("No records found in dataset")
            return jsonify({
                'success': False,
                'error': 'No records found in dataset'
            })
        
        print(f"Found {len(records)} records in dataset")
        
        # Create test database path
        test_db_path = f"test_databases/{test_db_name}.db"
        
        # Ensure test_databases directory exists
        os.makedirs("test_databases", exist_ok=True)
        
        print(f"Test database path: {test_db_path}")
        
        # Get storage manager for test database
        storage_manager = get_storage_manager(test_db_path)
        
        # Create table from schema
        schema_definition = dataset['schema_definition']
        table_name = schema_definition.get('name', f'dataset_{dataset_id}').lower().replace(' ', '_')
        
        print(f"Table name: {table_name}")
        
        # Create table
        table_created = storage_manager.create_table_from_schema(table_name, schema_definition)
        
        if not table_created:
            print("Failed to create table")
            return jsonify({
                'success': False,
                'error': 'Failed to create table in test database'
            })
        
        print("Table created successfully")
        
        # Convert records to the format expected by SQLite storage
        converted_records = []
        for record in records:
            converted_record = {
                'data': record['record_data'],
                'is_valid': record['is_valid'],
                'validation_errors': record['validation_errors'],
                'generation_metadata': record['generation_metadata']
            }
            converted_records.append(converted_record)
        
        print(f"Converted {len(converted_records)} records")
        
        # Insert data
        insert_result = storage_manager.insert_data(
            table_name=table_name,
            data=converted_records,
            schema_definition=schema_definition
        )
        
        print(f"Insert result: {insert_result}")
        
        if not insert_result.get('success'):
            print(f"Failed to insert data: {insert_result}")
            return jsonify({
                'success': False,
                'error': f'Failed to insert data: {insert_result.get("message", "Unknown error")}'
            })
        
        # Get table statistics
        table_info = storage_manager.get_table_info(table_name)
        
        print(f"Table info: {table_info}")
        
        result = {
            'success': True,
            'message': f'Successfully applied dataset "{dataset["name"]}" to test database',
            'test_database': {
                'name': test_db_name,
                'path': test_db_path,
                'table_name': table_name,
                'record_count': insert_result['inserted_count'],
                'table_info': table_info,
                'source_dataset': {
                    'id': dataset_id,
                    'name': dataset['name'],
                    'description': dataset['description']
                }
            }
        }
        
        print(f"Returning result: {result}")
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in apply_dataset_to_test_database: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/database/stats', methods=['GET'])
def get_database_stats():
    """Get database statistics"""
    try:
        db_manager = get_db_manager()
        stats = db_manager.get_dataset_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


# SQLite Storage Endpoints
@app.route('/api/sqlite/tables', methods=['GET'])
def get_sqlite_tables():
    """Get list of tables in SQLite database"""
    try:
        storage_manager = get_storage_manager()
        tables = storage_manager.list_tables()
        
        return jsonify({
            'success': True,
            'tables': tables
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/sqlite/table/<table_name>', methods=['GET'])
def get_sqlite_table_info(table_name):
    """Get information about a specific table"""
    try:
        storage_manager = get_storage_manager()
        table_info = storage_manager.get_table_info(table_name)
        
        if not table_info:
            return jsonify({
                'success': False,
                'error': f'Table {table_name} not found'
            })
        
        return jsonify({
            'success': True,
            'table_info': table_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/sqlite/table/<table_name>/data', methods=['GET'])
def get_sqlite_table_data(table_name):
    """Get data from a specific table"""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        storage_manager = get_storage_manager()
        data = storage_manager.query_data(table_name, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'data': data,
            'table_name': table_name,
            'limit': limit,
            'offset': offset,
            'count': len(data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/sqlite/export/<table_name>', methods=['GET'])
def export_sqlite_table(table_name):
    """Export table data as CSV"""
    try:
        storage_manager = get_storage_manager()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            success = storage_manager.export_to_csv(table_name, tmp_file.name)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': f'Failed to export table {table_name}'
                })
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'{table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mimetype='text/csv'
            )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/sqlite/stats', methods=['GET'])
def get_sqlite_stats():
    """Get SQLite database statistics"""
    try:
        storage_manager = get_storage_manager()
        stats = storage_manager.get_database_stats()
        
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })



    """Apply generated data to a new test database"""
    try:
        data = request.get_json()
        records = data.get('records', [])
        schema_data = data.get('schema', {})
        test_db_name = data.get('test_db_name', f'test_db_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        sql_dialect = data.get('sql_dialect', 'sqlite')  # Default to SQLite
        
        if not records:
            return jsonify({
                'success': False,
                'error': 'No records to apply to test database'
            })
        
        # If SQL dialect is not SQLite, generate SQL script instead of creating database
        if sql_dialect.lower() != 'sqlite':
            try:
                generator = SQLDialectGenerator(sql_dialect)
                
                # Handle multi-table schemas
                if isinstance(schema_data, dict) and 'tables' in schema_data:
                    # Multi-table schema
                    tables_data = {}
                    for table_def in schema_data['tables']:
                        table_name = table_def.get('name', 'table')
                        table_data = records.get(table_name, [])
                        
                        # Convert records to plain dictionaries if needed
                        plain_records = []
                        for record in table_data:
                            if isinstance(record, dict) and 'data' in record:
                                plain_records.append(record['data'])
                            elif hasattr(record, 'data'):
                                plain_records.append(record.data)
                            else:
                                plain_records.append(record)
                        
                        tables_data[table_name] = {
                            'schema': table_def,
                            'records': plain_records
                        }
                    
                    sql_script = generator.generate_multi_table_script(tables_data)
                else:
                    # Single table schema
                    table_name = schema_data.get('name', 'test_data')
                    
                    # Convert records to plain dictionaries if needed
                    plain_records = []
                    for record in records:
                        if isinstance(record, dict) and 'data' in record:
                            plain_records.append(record['data'])
                        elif hasattr(record, 'data'):
                            plain_records.append(record.data)
                        else:
                            plain_records.append(record)
                    
                    sql_script = generator.generate_complete_script(table_name, schema_data, plain_records)
                
                # Create temporary file for SQL script
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{sql_dialect}.sql', delete=False) as tmp_file:
                    tmp_file.write(sql_script)
                    tmp_filename = tmp_file.name
                
                return send_file(
                    tmp_filename,
                    as_attachment=True,
                    download_name=f'{test_db_name}_{sql_dialect}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql',
                    mimetype='text/plain'
                )
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to generate SQL script for {sql_dialect}: {str(e)}'
                })
        
        # SQLite database creation (existing logic)
        # Create test database path
        test_db_path = f"test_databases/{test_db_name}.db"
        
        # Ensure test_databases directory exists
        os.makedirs("test_databases", exist_ok=True)
        
        # Get storage manager for test database
        storage_manager = get_storage_manager(test_db_path)
        
        # Handle multi-table schemas
        if isinstance(schema_data, dict) and 'tables' in schema_data:
            # Multi-table schema
            tables_created = []
            total_records = 0
            
            for table_def in schema_data['tables']:
                table_name = table_def.get('name', 'table').lower().replace(' ', '_')
                
                # Create table
                table_created = storage_manager.create_table_from_schema(table_name, table_def)
                
                if table_created:
                    # Find corresponding data for this table
                    table_data = records.get(table_name, [])
                    
                    if table_data:
                        # Insert data
                        insert_result = storage_manager.insert_data(
                            table_name=table_name,
                            data=table_data,
                            schema_definition=table_def
                        )
                        
                        if insert_result.get('success'):
                            total_records += insert_result['inserted_count']
                            tables_created.append({
                                'name': table_name,
                                'record_count': insert_result['inserted_count']
                            })
            
            return jsonify({
                'success': True,
                'message': f'Successfully applied multi-table data to test database "{test_db_name}"',
                'test_database': {
                    'name': test_db_name,
                    'path': test_db_path,
                    'tables': tables_created,
                    'total_records': total_records
                }
            })
        else:
            # Single table schema (existing logic)
            table_name = schema_data.get('name', 'test_data').lower().replace(' ', '_')
            
            # Create schema definition for table creation
            schema_definition = {
                'name': table_name,
                'fields': schema_data.get('fields', [])
            }
            
            # Create table
            table_created = storage_manager.create_table_from_schema(table_name, schema_definition)
            
            if not table_created:
                return jsonify({
                    'success': False,
                    'error': 'Failed to create table in test database'
                })
            
            # Insert data
            insert_result = storage_manager.insert_data(
                table_name=table_name,
                data=records,
                schema_definition=schema_definition
            )
            
            if not insert_result.get('success'):
                return jsonify({
                    'success': False,
                    'error': f'Failed to insert data: {insert_result.get("message", "Unknown error")}'
                })
            
            # Get table statistics
            table_info = storage_manager.get_table_info(table_name)
            
            return jsonify({
                'success': True,
                'message': f'Successfully applied {insert_result["inserted_count"]} records to test database',
                'test_database': {
                    'name': test_db_name,
                    'path': test_db_path,
                    'table_name': table_name,
                    'record_count': insert_result['inserted_count'],
                    'table_info': table_info
                }
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/test-database/<db_name>/query', methods=['GET'])
def query_test_database(db_name):
    """Query data from a test database"""
    try:
        table_name = request.args.get('table', 'test_data')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Construct database path
        test_db_path = f"test_databases/{db_name}.db"
        
        if not os.path.exists(test_db_path):
            return jsonify({
                'success': False,
                'error': f'Test database {db_name} not found'
            })
        
        # Get storage manager
        storage_manager = get_storage_manager(test_db_path)
        
        # Query data
        data = storage_manager.query_data(table_name, limit=limit, offset=offset)
        
        # Get table info
        table_info = storage_manager.get_table_info(table_name)
        
        return jsonify({
            'success': True,
            'data': data,
            'table_info': table_info,
            'query_params': {
                'limit': limit,
                'offset': offset,
                'total_records': table_info.get('record_count', 0)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/test-database/<db_name>/export', methods=['GET'])
def export_test_database(db_name):
    """Export test database table as CSV"""
    try:
        table_name = request.args.get('table', 'test_data')
        
        # Construct database path
        test_db_path = f"test_databases/{db_name}.db"
        
        if not os.path.exists(test_db_path):
            return jsonify({
                'success': False,
                'error': f'Test database {db_name} not found'
            })
        
        # Get storage manager
        storage_manager = get_storage_manager(test_db_path)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            success = storage_manager.export_to_csv(table_name, tmp_file.name)
            
            if not success:
                return jsonify({
                    'success': False,
                    'error': f'Failed to export table {table_name}'
                })
            
            return send_file(
                tmp_file.name,
                as_attachment=True,
                download_name=f'{db_name}_{table_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                mimetype='text/csv'
            )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/test-database/<db_name>/save', methods=['POST'])
def save_test_database_to_new_db(db_name):
    """Save test database data to a new database with SQL dialect support"""
    try:
        data = request.get_json()
        new_db_name = data.get('new_db_name', f'{db_name}_copy_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
        sql_dialect = data.get('sql_dialect', 'sqlite')
        table_name = data.get('table_name', 'test_data')
        
        # Get source database path
        source_db_path = f"test_databases/{db_name}.db"
        
        if not os.path.exists(source_db_path):
            return jsonify({
                'success': False,
                'error': f'Test database {db_name} not found'
            })
        
        # Get storage manager for source database
        source_storage = get_storage_manager(source_db_path)
        
        # Get all data from the source table
        source_data = source_storage.query_data(table_name, limit=None)
        table_info = source_storage.get_table_info(table_name)
        
        if not source_data:
            return jsonify({
                'success': False,
                'error': f'No data found in table {table_name}'
            })
        
        # If SQL dialect is not SQLite, generate SQL script
        if sql_dialect.lower() != 'sqlite':
            try:
                generator = SQLDialectGenerator(sql_dialect)
                
                # Create a basic schema definition from table info
                schema_definition = {
                    'name': table_name,
                    'fields': []
                }
                
                # Try to infer field types from the data
                if source_data and len(source_data) > 0:
                    first_record = source_data[0]
                    for field_name, field_value in first_record.items():
                        field_type = 'string'  # Default
                        if isinstance(field_value, int):
                            field_type = 'integer'
                        elif isinstance(field_value, float):
                            field_type = 'float'
                        elif isinstance(field_value, bool):
                            field_type = 'boolean'
                        elif isinstance(field_value, (datetime, date)):
                            field_type = 'datetime'
                        
                        schema_definition['fields'].append({
                            'name': field_name,
                            'type': field_type,
                            'required': True
                        })
                
                sql_script = generator.generate_complete_script(table_name, schema_definition, source_data)
                
                # Create temporary file for SQL script
                with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{sql_dialect}.sql', delete=False) as tmp_file:
                    tmp_file.write(sql_script)
                    tmp_filename = tmp_file.name
                
                return send_file(
                    tmp_filename,
                    as_attachment=True,
                    download_name=f'{new_db_name}_{sql_dialect}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql',
                    mimetype='text/plain'
                )
                
            except Exception as e:
                return jsonify({
                    'success': False,
                    'error': f'Failed to generate SQL script for {sql_dialect}: {str(e)}'
                })
        
        # SQLite database creation
        new_db_path = f"test_databases/{new_db_name}.db"
        
        # Ensure test_databases directory exists
        os.makedirs("test_databases", exist_ok=True)
        
        # Get storage manager for new database
        new_storage = get_storage_manager(new_db_path)
        
        # Create basic schema definition from table info
        schema_definition = {
            'name': table_name,
            'fields': []
        }
        
        # Try to infer field types from the data
        if source_data and len(source_data) > 0:
            first_record = source_data[0]
            for field_name, field_value in first_record.items():
                field_type = 'string'  # Default
                if isinstance(field_value, int):
                    field_type = 'integer'
                elif isinstance(field_value, float):
                    field_type = 'float'
                elif isinstance(field_value, bool):
                    field_type = 'boolean'
                
                schema_definition['fields'].append({
                    'name': field_name,
                    'data_type': field_type.upper(),
                    'required': True
                })
        
        # Create table in new database
        table_created = new_storage.create_table_from_schema(table_name, schema_definition)
        
        if not table_created:
            return jsonify({
                'success': False,
                'error': 'Failed to create table in new database'
            })
        
        # Convert data format for insertion
        converted_records = []
        for record in source_data:
            converted_record = {
                'data': record,
                'is_valid': True,
                'validation_errors': [],
                'generation_metadata': {}
            }
            converted_records.append(converted_record)
        
        # Insert data into new database
        insert_result = new_storage.insert_data(
            table_name=table_name,
            data=converted_records,
            schema_definition=schema_definition
        )
        
        if not insert_result.get('success'):
            return jsonify({
                'success': False,
                'error': f'Failed to insert data: {insert_result.get("message", "Unknown error")}'
            })
        
        return jsonify({
            'success': True,
            'message': f'Successfully saved test database "{db_name}" to new database "{new_db_name}"',
            'new_database': {
                'name': new_db_name,
                'path': new_db_path,
                'table_name': table_name,
                'record_count': insert_result['inserted_count'],
                'source_database': db_name
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/test-database/<db_name>/delete', methods=['DELETE'])
def delete_test_database(db_name):
    """Delete a test database"""
    try:
        db_path = os.path.join('test_databases', f'{db_name}.db')
        if not os.path.exists(db_path):
            return jsonify({'success': False, 'error': 'Test database not found'})
        
        # Remove the database file
        os.remove(db_path)
        
        return jsonify({
            'success': True, 
            'message': f'Test database "{db_name}" deleted successfully'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/test-databases', methods=['GET'])
def list_test_databases():
    """List all test databases"""
    try:
        test_db_dir = "test_databases"
        
        print(f"Checking test database directory: {test_db_dir}")
        print(f"Directory exists: {os.path.exists(test_db_dir)}")
        
        if not os.path.exists(test_db_dir):
            print("Test database directory does not exist, creating it...")
            os.makedirs(test_db_dir, exist_ok=True)
            return jsonify({
                'success': True,
                'databases': []
            })
        
        databases = []
        files = os.listdir(test_db_dir)
        print(f"Found files in test_databases: {files}")
        
        for filename in files:
            if filename.endswith('.db'):
                db_name = filename[:-3]  # Remove .db extension
                db_path = os.path.join(test_db_dir, filename)
                
                print(f"Processing database: {db_name} at {db_path}")
                
                # Get basic info about the database
                try:
                    storage_manager = get_storage_manager(db_path)
                    stats = storage_manager.get_database_stats()
                    print(f"Database stats for {db_name}: {stats}")
                    
                    databases.append({
                        'name': db_name,
                        'path': db_path,
                        'tables': stats.get('tables', []),
                        'total_records': stats.get('total_records', 0),
                        'created_at': datetime.fromtimestamp(os.path.getctime(db_path)).isoformat()
                    })
                except Exception as e:
                    print(f"Error reading database {db_name}: {e}")
                    # Skip databases that can't be read
                    continue
        
        print(f"Returning {len(databases)} databases")
        return jsonify({
            'success': True,
            'databases': databases
        })
        
    except Exception as e:
        print(f"Error in list_test_databases: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/schema-templates', methods=['GET'])
def list_schema_templates():
    """List schema templates"""
    try:
        category = request.args.get('category')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        db_manager = get_db_manager()
        templates = db_manager.get_schema_templates(category=category, limit=limit, offset=offset)
        
        return jsonify({
            'success': True,
            'templates': templates
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/schema-templates', methods=['POST'])
def create_schema_template():
    """Create a new schema template"""
    try:
        data = request.get_json()
        
        name = data.get('name')
        description = data.get('description', '')
        category = data.get('category', 'custom')
        schema_definition = data.get('schema_definition')
        
        if not name or not schema_definition:
            return jsonify({
                'success': False,
                'error': 'Name and schema_definition are required'
            }), 400
        
        db_manager = get_db_manager()
        template = db_manager.create_schema_template(name, description, category, schema_definition)
        
        return jsonify({
            'success': True,
            'template': template
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/schema-templates/<int:template_id>', methods=['GET'])
def get_schema_template(template_id):
    """Get a schema template by ID"""
    try:
        db_manager = get_db_manager()
        template = db_manager.get_schema_template(template_id)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Schema template not found'
            }), 404
        
        return jsonify({
            'success': True,
            'template': template
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/schema-templates/<int:template_id>', methods=['PUT'])
def update_schema_template(template_id):
    """Update a schema template"""
    try:
        data = request.get_json()
        
        db_manager = get_db_manager()
        template = db_manager.update_schema_template(template_id, **data)
        
        if not template:
            return jsonify({
                'success': False,
                'error': 'Schema template not found'
            }), 404
        
        return jsonify({
            'success': True,
            'template': template
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/schema-templates/<int:template_id>', methods=['DELETE'])
def delete_schema_template(template_id):
    """Delete a schema template"""
    try:
        db_manager = get_db_manager()
        success = db_manager.delete_schema_template(template_id)
        
        if not success:
            return jsonify({
                'success': False,
                'error': 'Schema template not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Schema template deleted successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/generate-sql', methods=['POST'])
def generate_sql():
    """Generate SQL INSERT statements for different database dialects"""
    try:
        data = request.get_json()
        dialect = data.get('dialect')
        records_data = data.get('data')
        schema = data.get('schema')
        
        if not dialect:
            return jsonify({'success': False, 'error': 'Database dialect is required'})
        
        if not records_data:
            return jsonify({'success': False, 'error': 'No data provided for SQL generation'})
        
        from src.sql_dialect_generator import SQLDialectGenerator
        
        sql_generator = SQLDialectGenerator(dialect)
        
        sql_statements = {}
        
        if isinstance(records_data, dict):
            for table_name, records in records_data.items():
                sql_statements[table_name] = sql_generator.generate_insert_statements(table_name, records)
        else:
            table_name = schema.get('name', 'table') if schema else 'table'
            sql_statements = sql_generator.generate_insert_statements(table_name, records_data)
        
        return jsonify({
            'success': True,
            'sql_statements': sql_statements,
            'dialect': dialect
        })
        
    except Exception as e:
        logger.error(f"SQL generation failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generate-sql-llm', methods=['POST'])
def generate_sql_llm():
    """Generate SQL using LLM for different database dialects"""
    try:
        data = request.get_json()
        dialect = data.get('dialect')
        records_data = data.get('data')
        schema = data.get('schema')
        table_name = data.get('table_name', 'generated_table')
        description = data.get('description', '')
        
        if not dialect:
            return jsonify({'success': False, 'error': 'Database dialect is required'})
        
        if not records_data:
            return jsonify({'success': False, 'error': 'No data provided for SQL generation'})
        
        # Initialize LLM SQL generator
        llm_generator = LLMSQLGenerator(dialect)
        
        # Convert records to list format if needed
        if isinstance(records_data, dict):
            # Multi-table data
            sql_statements = {}
            for table_name, records in records_data.items():
                sql_content = llm_generator.generate_sql_from_data(
                    table_name, schema, records, description
                )
                sql_statements[table_name] = sql_content
        else:
            # Single table data
            sql_content = llm_generator.generate_sql_from_data(
                table_name, schema, records_data, description
            )
            sql_statements = {table_name: sql_content}
        
        return jsonify({
            'success': True,
            'sql_statements': sql_statements,
            'dialect': dialect,
            'table_name': table_name
        })
        
    except Exception as e:
        logger.error(f"LLM SQL generation failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/save-generated-sql', methods=['POST'])
def save_generated_sql():
    """Save generated SQL to database"""
    try:
        data = request.get_json()
        name = data.get('name')
        description = data.get('description', '')
        dataset_id = data.get('dataset_id')
        dialect = data.get('dialect')
        sql_content = data.get('sql_content')
        schema_definition = data.get('schema_definition', {})
        record_count = data.get('record_count', 0)
        
        if not all([name, dataset_id, dialect, sql_content]):
            return jsonify({
                'success': False, 
                'error': 'Missing required fields: name, dataset_id, dialect, sql_content'
            })
        
        # Save to database
        db_manager = get_db_manager()
        saved_sql = db_manager.save_generated_sql(
            name=name,
            description=description,
            dataset_id=dataset_id,
            dialect=dialect,
            sql_content=sql_content,
            schema_definition=schema_definition,
            record_count=record_count
        )
        
        return jsonify({
            'success': True,
            'message': 'SQL saved successfully',
            'generated_sql': saved_sql
        })
        
    except Exception as e:
        logger.error(f"Failed to save generated SQL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generated-sql', methods=['GET'])
def list_generated_sql():
    """List all generated SQL records"""
    try:
        page = request.args.get('page', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        dataset_id = request.args.get('dataset_id', type=int)
        
        db_manager = get_db_manager()
        
        if dataset_id:
            sql_records = db_manager.get_generated_sql_by_dataset(dataset_id, limit, page * limit)
        else:
            sql_records = db_manager.get_all_generated_sql(limit, page * limit)
        
        return jsonify({
            'success': True,
            'generated_sql': sql_records
        })
        
    except Exception as e:
        logger.error(f"Failed to list generated SQL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generated-sql/<int:sql_id>', methods=['GET'])
def get_generated_sql(sql_id):
    """Get specific generated SQL record"""
    try:
        db_manager = get_db_manager()
        sql_record = db_manager.get_generated_sql(sql_id)
        
        if not sql_record:
            return jsonify({'success': False, 'error': 'Generated SQL not found'}), 404
        
        return jsonify({
            'success': True,
            'generated_sql': sql_record
        })
        
    except Exception as e:
        logger.error(f"Failed to get generated SQL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generated-sql/<int:sql_id>', methods=['DELETE'])
def delete_generated_sql(sql_id):
    """Delete generated SQL record"""
    try:
        db_manager = get_db_manager()
        success = db_manager.delete_generated_sql(sql_id)
        
        if not success:
            return jsonify({'success': False, 'error': 'Generated SQL not found'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Generated SQL deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Failed to delete generated SQL: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("🚀 Starting Synthetic Data Generation Web App")
    print("=" * 50)
    print("📋 Available endpoints:")
    print("   - / (Dashboard)")
    print("   - /api/config (Configuration)")
    print("   - /api/generate (Generate Data)")
    print("   - /api/export/csv (Export CSV)")
    print("   - /api/export/json (Export JSON)")
    print("   - /api/generate-sql (Generate SQL Statements)")
    print("   - /api/generate-sql-llm (Generate SQL using LLM)")
    print("   - /api/save-generated-sql (Save generated SQL)")
    print("   - /api/generated-sql (List generated SQL)")
    print("   - /api/generated-sql/<id> (Get/Delete generated SQL)")
    print("   - /api/schema-templates (Schema Templates from Admin)")
    print("   - /api/validate-schema (Validate Schema)")
    print("   📊 Database endpoints:")
    print("   - /api/datasets (List saved datasets)")
    print("   - /api/datasets/<id> (Get dataset details)")
    print("   - /api/datasets/<id>/records (Get dataset records)")
    print("   - /api/datasets/<id>/export/csv (Export dataset as CSV)")
    print("   - /api/datasets/<id>/search (Search records)")

    print("   - /api/database/stats (Database statistics)")
    print("   🗄️ SQLite Storage endpoints:")
    print("   - /api/sqlite/tables (List SQLite tables)")
    print("   - /api/sqlite/table/<name> (Get table info)")
    print("   - /api/sqlite/table/<name>/data (Get table data)")
    print("   - /api/sqlite/export/<name> (Export table as CSV)")
    print("   - /api/sqlite/stats (SQLite database stats)")
    print("   🔧 Schema Admin endpoints:")
    print("   - /api/schema-templates (List/Create schema templates)")
    print("   - /api/schema-templates/<id> (Get/Update/Delete schema template)")
    print()
    print("🌐 Open your browser and go to: http://localhost:5001")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
