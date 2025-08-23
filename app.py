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
from src.synthetic_data_generator import SyntheticDataGenerator
from src.groq_config import GroqConfig
from src.database import init_database, get_db_manager


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


@app.route('/api/config')
def get_config():
    """Get current configuration"""
    try:
        config = EnvConfig.validate_config()
        models = GroqConfig.list_models()
        
        return jsonify({
            'success': True,
            'config': config,
            'models': models,
            'temperature_presets': GroqConfig.TEMPERATURE_PRESETS
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
        
        # Generate data
        results = generator.generate_data(schema)
        
        if isinstance(results, dict) and 'error' in results:
            return jsonify({
                'success': False,
                'error': results['error']
            })
        
        # Save to database if requested
        save_to_db = generation_params.get('save_to_database', True)
        dataset_id = None
        
        if save_to_db:
            try:
                db_manager = get_db_manager()
                dataset_id = db_manager.save_dataset(
                    name=schema.name,
                    description=schema.description or '',
                    schema_definition=schema.dict(),
                    records=results.get('generated_records', []),
                    generation_metadata=results.get('generation_metadata', {}),
                    quality_metrics=results.get('quality_metrics', {})
                )
            except Exception as db_error:
                print(f"Warning: Failed to save to database: {db_error}")
        
        # Prepare response - SyntheticDataGenerator returns a dictionary
        response_data = {
            'success': True,
            'generated_records': results.get('generated_records', []),
            'quality_metrics': results.get('quality_metrics', {}),
            'generation_metadata': results.get('generation_metadata', {}),
            'total_records': len(results.get('generated_records', [])),
            'dataset_id': dataset_id,
            'saved_to_database': save_to_db and dataset_id is not None
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
        
        # Convert to DataFrame
        df = pd.DataFrame([record['data'] for record in records])
        
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


@app.route('/api/schema/templates')
def get_schema_templates():
    """Get predefined schema templates"""
    templates = {
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
    
    return jsonify({
        'success': True,
        'templates': templates
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

@app.route('/api/datasets', methods=['GET'])
def get_datasets():
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


if __name__ == '__main__':
    print("🚀 Starting Synthetic Data Generation Web App")
    print("=" * 50)
    print("📋 Available endpoints:")
    print("   - / (Dashboard)")
    print("   - /api/config (Configuration)")
    print("   - /api/generate (Generate Data)")
    print("   - /api/export/csv (Export CSV)")
    print("   - /api/export/json (Export JSON)")
    print("   - /api/schema/templates (Schema Templates)")
    print("   - /api/validate-schema (Validate Schema)")
    print("   📊 Database endpoints:")
    print("   - /api/datasets (List saved datasets)")
    print("   - /api/datasets/<id> (Get dataset details)")
    print("   - /api/datasets/<id>/records (Get dataset records)")
    print("   - /api/datasets/<id>/export/csv (Export dataset as CSV)")
    print("   - /api/datasets/<id>/search (Search records)")
    print("   - /api/database/stats (Database statistics)")
    print()
    print("🌐 Open your browser and go to: http://localhost:5001")
    print()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
