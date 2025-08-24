# Schema Administration System

## Overview

The Schema Administration system provides a comprehensive interface for creating, managing, and reusing schema templates. It supports both single-table and multi-table schemas, making it easy to define complex data structures for synthetic data generation.

## Features

### 🔧 **Schema Template Management**
- **Create**: Build new schema templates with multiple tables
- **Edit**: Modify existing templates with a visual interface
- **Delete**: Remove templates (soft delete)
- **Use**: Apply templates to the data generation form

### 📊 **Multi-Table Support**
- Define schemas with multiple related tables
- Support for complex data relationships
- Automatic table creation in test databases

### 🏷️ **Categorization**
- Organize templates by category (ecommerce, healthcare, finance, etc.)
- Easy filtering and management

### 🔄 **Template Reusability**
- Save commonly used schemas as templates
- Quick application to data generation workflow
- Consistent schema definitions across projects

## UI Components

### Schema Admin Tab
Located in the main navigation, the Schema Admin tab provides:

- **Template List**: View all available schema templates
- **Create Button**: Open the schema creation modal
- **Refresh Button**: Reload the template list
- **Template Cards**: Display template details with action buttons

### Schema Creation/Edit Modal
A comprehensive modal for schema management:

- **Basic Info**: Name, description, and category
- **Table Management**: Add/remove tables with fields
- **Field Configuration**: Define field types and requirements
- **Validation**: Real-time schema validation

## API Endpoints

### Schema Templates

#### `GET /api/schema-templates`
List all schema templates with optional filtering.

**Query Parameters:**
- `category` (optional): Filter by category
- `limit` (optional): Number of templates to return (default: 50)
- `offset` (optional): Pagination offset (default: 0)

**Response:**
```json
{
  "success": true,
  "templates": [
    {
      "id": 1,
      "name": "E-commerce Multi-Table",
      "description": "Complete e-commerce schema",
      "category": "ecommerce",
      "schema_definition": {
        "name": "ecommerce_schema",
        "tables": [...]
      },
      "created_at": "2025-08-23T16:00:00",
      "updated_at": "2025-08-23T16:00:00",
      "is_active": true
    }
  ]
}
```

#### `POST /api/schema-templates`
Create a new schema template.

**Request Body:**
```json
{
  "name": "Template Name",
  "description": "Template description",
  "category": "ecommerce",
  "schema_definition": {
    "name": "schema_name",
    "tables": [
      {
        "name": "table_name",
        "display_name": "Table Display Name",
        "fields": [
          {
            "name": "field_name",
            "type": "STRING",
            "required": true
          }
        ]
      }
    ]
  }
}
```

#### `GET /api/schema-templates/<id>`
Get a specific schema template by ID.

#### `PUT /api/schema-templates/<id>`
Update an existing schema template.

#### `DELETE /api/schema-templates/<id>`
Delete a schema template (soft delete).

## Schema Definition Structure

### Single Table Schema
```json
{
  "name": "user_data",
  "description": "User information schema",
  "fields": [
    {
      "name": "user_id",
      "type": "INTEGER",
      "required": true
    },
    {
      "name": "name",
      "type": "STRING",
      "required": true
    },
    {
      "name": "email",
      "type": "EMAIL",
      "required": true
    }
  ]
}
```

### Multi-Table Schema
```json
{
  "name": "ecommerce_schema",
  "description": "Multi-table e-commerce schema",
  "tables": [
    {
      "name": "products",
      "display_name": "Products",
      "fields": [
        {
          "name": "product_id",
          "type": "INTEGER",
          "required": true
        },
        {
          "name": "name",
          "type": "STRING",
          "required": true
        },
        {
          "name": "price",
          "type": "FLOAT",
          "required": true
        }
      ]
    },
    {
      "name": "customers",
      "display_name": "Customers",
      "fields": [
        {
          "name": "customer_id",
          "type": "INTEGER",
          "required": true
        },
        {
          "name": "name",
          "type": "STRING",
          "required": true
        },
        {
          "name": "email",
          "type": "EMAIL",
          "required": true
        }
      ]
    }
  ]
}
```

## Field Types

The system supports the following field types:

- **STRING**: Text data
- **INTEGER**: Whole numbers
- **FLOAT**: Decimal numbers
- **BOOLEAN**: True/false values
- **DATE**: Date values
- **DATETIME**: Date and time values
- **EMAIL**: Email addresses
- **PHONE**: Phone numbers
- **ADDRESS**: Address information
- **NAME**: Person names

## Usage Workflow

### 1. Creating a Schema Template

1. Navigate to the **Schema Admin** tab
2. Click **"New Schema"** button
3. Fill in basic information (name, description, category)
4. Add tables using the **"Add Table"** button
5. For each table:
   - Set table name and display name
   - Add fields with appropriate types
   - Mark required fields
6. Click **"Save Schema"** to create the template

### 2. Using a Schema Template

1. In the **Schema Admin** tab, find the desired template
2. Click the **"Use"** button
3. The application will switch to the **Generated Data** tab
4. The schema will be automatically applied to the form
5. Generate data using the template

### 3. Editing a Schema Template

1. In the **Schema Admin** tab, find the template to edit
2. Click the **"Edit"** button
3. Modify the schema in the modal
4. Click **"Save Schema"** to update the template

### 4. Multi-Table Data Generation

1. Create or use a multi-table schema template
2. Generate data (currently supports first table)
3. Apply to test database
4. Multiple tables will be created in the test database

## Test Database Integration

When applying multi-table schemas to test databases:

- Each table in the schema creates a separate table in the test database
- Data is inserted into the appropriate tables
- The system provides statistics for all created tables
- Test databases can be queried and exported

## Database Schema

### Schema Templates Table
```sql
CREATE TABLE schema_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    category VARCHAR(100) DEFAULT 'custom',
    schema_definition JSON NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

## Examples

### E-commerce Schema
```json
{
  "name": "E-commerce Complete",
  "description": "Complete e-commerce system with products, customers, orders, and order items",
  "category": "ecommerce",
  "schema_definition": {
    "name": "ecommerce_complete",
    "tables": [
      {
        "name": "products",
        "display_name": "Products",
        "fields": [
          {"name": "product_id", "type": "INTEGER", "required": true},
          {"name": "name", "type": "STRING", "required": true},
          {"name": "description", "type": "STRING", "required": false},
          {"name": "price", "type": "FLOAT", "required": true},
          {"name": "category", "type": "STRING", "required": false},
          {"name": "stock_quantity", "type": "INTEGER", "required": true}
        ]
      },
      {
        "name": "customers",
        "display_name": "Customers",
        "fields": [
          {"name": "customer_id", "type": "INTEGER", "required": true},
          {"name": "first_name", "type": "STRING", "required": true},
          {"name": "last_name", "type": "STRING", "required": true},
          {"name": "email", "type": "EMAIL", "required": true},
          {"name": "phone", "type": "PHONE", "required": false},
          {"name": "address", "type": "ADDRESS", "required": false}
        ]
      },
      {
        "name": "orders",
        "display_name": "Orders",
        "fields": [
          {"name": "order_id", "type": "INTEGER", "required": true},
          {"name": "customer_id", "type": "INTEGER", "required": true},
          {"name": "order_date", "type": "DATETIME", "required": true},
          {"name": "status", "type": "STRING", "required": true},
          {"name": "total_amount", "type": "FLOAT", "required": true}
        ]
      },
      {
        "name": "order_items",
        "display_name": "Order Items",
        "fields": [
          {"name": "order_item_id", "type": "INTEGER", "required": true},
          {"name": "order_id", "type": "INTEGER", "required": true},
          {"name": "product_id", "type": "INTEGER", "required": true},
          {"name": "quantity", "type": "INTEGER", "required": true},
          {"name": "unit_price", "type": "FLOAT", "required": true},
          {"name": "total_price", "type": "FLOAT", "required": true}
        ]
      }
    ]
  }
}
```

### Healthcare Schema
```json
{
  "name": "Healthcare System",
  "description": "Healthcare management system with patients, doctors, and appointments",
  "category": "healthcare",
  "schema_definition": {
    "name": "healthcare_system",
    "tables": [
      {
        "name": "patients",
        "display_name": "Patients",
        "fields": [
          {"name": "patient_id", "type": "INTEGER", "required": true},
          {"name": "first_name", "type": "STRING", "required": true},
          {"name": "last_name", "type": "STRING", "required": true},
          {"name": "date_of_birth", "type": "DATE", "required": true},
          {"name": "email", "type": "EMAIL", "required": false},
          {"name": "phone", "type": "PHONE", "required": true},
          {"name": "address", "type": "ADDRESS", "required": false}
        ]
      },
      {
        "name": "doctors",
        "display_name": "Doctors",
        "fields": [
          {"name": "doctor_id", "type": "INTEGER", "required": true},
          {"name": "first_name", "type": "STRING", "required": true},
          {"name": "last_name", "type": "STRING", "required": true},
          {"name": "specialization", "type": "STRING", "required": true},
          {"name": "email", "type": "EMAIL", "required": true},
          {"name": "phone", "type": "PHONE", "required": true}
        ]
      },
      {
        "name": "appointments",
        "display_name": "Appointments",
        "fields": [
          {"name": "appointment_id", "type": "INTEGER", "required": true},
          {"name": "patient_id", "type": "INTEGER", "required": true},
          {"name": "doctor_id", "type": "INTEGER", "required": true},
          {"name": "appointment_date", "type": "DATETIME", "required": true},
          {"name": "status", "type": "STRING", "required": true},
          {"name": "notes", "type": "STRING", "required": false}
        ]
      }
    ]
  }
}
```

## Best Practices

1. **Naming Conventions**: Use clear, descriptive names for schemas and tables
2. **Field Types**: Choose appropriate field types for data validation
3. **Required Fields**: Mark essential fields as required
4. **Categories**: Use categories to organize templates effectively
5. **Descriptions**: Provide clear descriptions for better template management
6. **Testing**: Test templates with small datasets before large-scale generation

## Future Enhancements

- **Schema Validation**: Enhanced validation rules and constraints
- **Relationship Mapping**: Define foreign key relationships between tables
- **Template Versioning**: Version control for schema templates
- **Import/Export**: Import/export templates in various formats
- **Template Sharing**: Share templates across different instances
- **Advanced Field Types**: Support for more complex data types
- **Schema Templates Library**: Pre-built templates for common use cases
