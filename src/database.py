"""
Database models and utilities for SQLite integration
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

Base = declarative_base()


class Dataset(Base):
    """Model for storing dataset metadata"""
    __tablename__ = 'datasets'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    schema_definition = Column(Text, nullable=False)  # JSON string of schema
    record_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generation_metadata = Column(Text)  # JSON string of metadata

    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'schema_definition': json.loads(self.schema_definition) if self.schema_definition else {},
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'generation_metadata': json.loads(self.generation_metadata) if self.generation_metadata else {},

        }


class DataRecord(Base):
    """Model for storing individual data records"""
    __tablename__ = 'data_records'
    
    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer, nullable=False)  # Foreign key to datasets
    record_data = Column(Text, nullable=False)  # JSON string of record data
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(Text)  # JSON string of validation errors
    generation_metadata = Column(Text)  # JSON string of generation metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'dataset_id': self.dataset_id,
            'record_data': json.loads(self.record_data) if self.record_data else {},
            'is_valid': self.is_valid,
            'validation_errors': json.loads(self.validation_errors) if self.validation_errors else [],
            'generation_metadata': json.loads(self.generation_metadata) if self.generation_metadata else {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SchemaTemplate(Base):
    """Schema template model for storing reusable schema definitions"""
    __tablename__ = 'schema_templates'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(100), default='custom')
    schema_definition = Column(JSON, nullable=False)  # Multi-table schema definition
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'schema_definition': self.schema_definition,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }


class GeneratedSQL(Base):
    """Model for storing generated SQL statements"""
    __tablename__ = 'generated_sql'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    dataset_id = Column(Integer, nullable=False)  # Foreign key to datasets
    dialect = Column(String(50), nullable=False)  # mysql, postgresql, sqlserver, oracle, db2
    sql_content = Column(Text, nullable=False)  # The generated SQL content
    schema_definition = Column(Text)  # JSON string of schema used
    record_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model instance to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'dataset_id': self.dataset_id,
            'dialect': self.dialect,
            'sql_content': self.sql_content,
            'schema_definition': json.loads(self.schema_definition) if self.schema_definition else {},
            'record_count': self.record_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DatabaseManager:
    """Database manager for SQLite operations"""
    
    def __init__(self, database_url: str = None):
        """Initialize database manager"""
        if database_url is None:
            # Default to SQLite file in the project directory
            database_url = f"sqlite:///{os.path.join(os.getcwd(), 'synthetic_data.db')}"
        
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        self.create_tables()
    
    def create_tables(self):
        """Create database tables"""
        Base.metadata.create_all(bind=self.engine)
    
    def get_session(self) -> Session:
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """Close database session"""
        session.close()
    
    def save_dataset(self, name: str, description: str, schema_definition: Dict[str, Any], 
                    records: List[Dict[str, Any]], generation_metadata: Dict[str, Any] = None) -> int:
        """
        Save a complete dataset with records
        
        Args:
            name: Dataset name
            description: Dataset description
            schema_definition: Schema definition dictionary
            records: List of generated records
            generation_metadata: Generation metadata
    
            
        Returns:
            Dataset ID
        """
        session = self.get_session()
        try:
            # Create dataset record
            dataset = Dataset(
                name=name,
                description=description,
                schema_definition=json.dumps(schema_definition),
                record_count=len(records),
                generation_metadata=json.dumps(generation_metadata or {}),
    
            )
            session.add(dataset)
            session.flush()  # Get the ID
            
            # Create data records
            for record in records:
                # Handle different record formats
                if isinstance(record, dict):
                    if 'data' in record:
                        # Record has a 'data' field (from generated data)
                        record_data = record.get('data', {})
                        is_valid = record.get('is_valid', True)
                        validation_errors = record.get('validation_errors', [])
                        generation_metadata = record.get('generation_metadata', {})
                    else:
                        # Record is the actual data (from save to dataset)
                        record_data = record
                        is_valid = True
                        validation_errors = []
                        generation_metadata = {}
                else:
                    # Fallback for other formats
                    record_data = record
                    is_valid = True
                    validation_errors = []
                    generation_metadata = {}
                
                data_record = DataRecord(
                    dataset_id=dataset.id,
                    record_data=json.dumps(record_data),
                    is_valid=is_valid,
                    validation_errors=json.dumps(validation_errors),
                    generation_metadata=json.dumps(generation_metadata)
                )
                session.add(data_record)
            
            session.commit()
            return dataset.id
            
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def get_datasets(self, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get list of datasets
        
        Args:
            limit: Maximum number of datasets to return
            offset: Number of datasets to skip
            
        Returns:
            List of dataset dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(Dataset).order_by(Dataset.created_at.desc())
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            datasets = query.all()
            return [dataset.to_dict() for dataset in datasets]
            
        finally:
            self.close_session(session)
    
    def get_dataset(self, dataset_id: int) -> Optional[Dict[str, Any]]:
        """
        Get dataset by ID
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            Dataset dictionary or None
        """
        session = self.get_session()
        try:
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            return dataset.to_dict() if dataset else None
        finally:
            self.close_session(session)
    
    def get_dataset_records(self, dataset_id: int, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get records for a dataset
        
        Args:
            dataset_id: Dataset ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of record dictionaries
        """
        session = self.get_session()
        try:
            query = session.query(DataRecord).filter(DataRecord.dataset_id == dataset_id).order_by(DataRecord.id)
            
            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)
            
            records = query.all()
            return [record.to_dict() for record in records]
            
        finally:
            self.close_session(session)
    
    def delete_dataset(self, dataset_id: int) -> bool:
        """
        Delete dataset and all its records
        
        Args:
            dataset_id: Dataset ID
            
        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        try:
            # Delete records first
            session.query(DataRecord).filter(DataRecord.dataset_id == dataset_id).delete()
            
            # Delete dataset
            dataset = session.query(Dataset).filter(Dataset.id == dataset_id).first()
            if dataset:
                session.delete(dataset)
                session.commit()
                return True
            else:
                return False
                
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def search_records(self, dataset_id: int, search_query: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search records in a dataset
        
        Args:
            dataset_id: Dataset ID
            search_query: Search query string
            limit: Maximum number of results
            
        Returns:
            List of matching record dictionaries
        """
        session = self.get_session()
        try:
            # Simple text search in record_data
            query = session.query(DataRecord).filter(
                DataRecord.dataset_id == dataset_id,
                DataRecord.record_data.contains(search_query)
            ).limit(limit)
            
            records = query.all()
            return [record.to_dict() for record in records]
            
        finally:
            self.close_session(session)
    
    def get_dataset_stats(self) -> Dict[str, Any]:
        """
        Get database statistics
        
        Returns:
            Dictionary with database statistics
        """
        session = self.get_session()
        try:
            total_datasets = session.query(Dataset).count()
            total_records = session.query(DataRecord).count()
            
            # Get recent datasets
            recent_datasets = session.query(Dataset).order_by(Dataset.created_at.desc()).limit(5).all()
            
            return {
                'total_datasets': total_datasets,
                'total_records': total_records,
                'recent_datasets': [dataset.to_dict() for dataset in recent_datasets],
                'database_file': self.database_url
            }
            
        finally:
            self.close_session(session)

    def create_schema_template(self, name: str, description: str, category: str, schema_definition: dict) -> dict:
        """Create a new schema template"""
        session = self.get_session()
        try:
            template = SchemaTemplate(
                name=name,
                description=description,
                category=category,
                schema_definition=schema_definition,
                is_active=True  # Explicitly set to True
            )
            session.add(template)
            session.commit()
            return template.to_dict()
        except Exception as e:
            session.rollback()
            raise e
    
    def get_schema_template(self, template_id: int) -> dict:
        """Get a schema template by ID"""
        session = self.get_session()
        template = session.query(SchemaTemplate).filter(
            SchemaTemplate.id == template_id,
            SchemaTemplate.is_active == True
        ).first()
        return template.to_dict() if template else None
    
    def get_schema_templates(self, category: str = None, limit: int = 50, offset: int = 0) -> list:
        """Get schema templates with optional filtering"""
        session = self.get_session()
        query = session.query(SchemaTemplate).filter(SchemaTemplate.is_active == True)
        
        if category:
            query = query.filter(SchemaTemplate.category == category)
        
        templates = query.order_by(SchemaTemplate.created_at.desc()).offset(offset).limit(limit).all()
        return [template.to_dict() for template in templates]
    
    def update_schema_template(self, template_id: int, **kwargs) -> dict:
        """Update a schema template"""
        session = self.get_session()
        try:
            template = session.query(SchemaTemplate).filter(SchemaTemplate.id == template_id).first()
            if not template:
                return None
            
            for key, value in kwargs.items():
                if hasattr(template, key):
                    setattr(template, key, value)
            
            template.updated_at = datetime.utcnow()
            session.commit()
            return template.to_dict()
        except Exception as e:
            session.rollback()
            raise e
    
    def delete_schema_template(self, template_id: int) -> bool:
        """Delete a schema template (soft delete)"""
        session = self.get_session()
        try:
            template = session.query(SchemaTemplate).filter(SchemaTemplate.id == template_id).first()
            if not template:
                return False
            
            template.is_active = False
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e

    # Generated SQL methods
    def save_generated_sql(self, name: str, description: str, dataset_id: int, dialect: str, 
                          sql_content: str, schema_definition: dict, record_count: int) -> dict:
        """Save generated SQL to database"""
        session = self.get_session()
        try:
            generated_sql = GeneratedSQL(
                name=name,
                description=description,
                dataset_id=dataset_id,
                dialect=dialect,
                sql_content=sql_content,
                schema_definition=json.dumps(schema_definition),
                record_count=record_count
            )
            session.add(generated_sql)
            session.commit()
            return generated_sql.to_dict()
        except Exception as e:
            session.rollback()
            raise e
    
    def get_generated_sql(self, sql_id: int) -> dict:
        """Get generated SQL by ID"""
        session = self.get_session()
        sql_record = session.query(GeneratedSQL).filter(GeneratedSQL.id == sql_id).first()
        return sql_record.to_dict() if sql_record else None
    
    def get_generated_sql_by_dataset(self, dataset_id: int, limit: int = 50, offset: int = 0) -> list:
        """Get generated SQL for a specific dataset"""
        session = self.get_session()
        sql_records = session.query(GeneratedSQL).filter(
            GeneratedSQL.dataset_id == dataset_id
        ).order_by(GeneratedSQL.created_at.desc()).offset(offset).limit(limit).all()
        return [record.to_dict() for record in sql_records]
    
    def get_all_generated_sql(self, limit: int = 50, offset: int = 0) -> list:
        """Get all generated SQL records"""
        session = self.get_session()
        sql_records = session.query(GeneratedSQL).order_by(
            GeneratedSQL.created_at.desc()
        ).offset(offset).limit(limit).all()
        return [record.to_dict() for record in sql_records]
    
    def delete_generated_sql(self, sql_id: int) -> bool:
        """Delete generated SQL record"""
        session = self.get_session()
        try:
            sql_record = session.query(GeneratedSQL).filter(GeneratedSQL.id == sql_id).first()
            if not sql_record:
                return False
            
            session.delete(sql_record)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e


# Global database manager instance
db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager

def init_database(app=None, database_url: str = None):
    """Initialize database for Flask app"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    
    if app:
        # Store database manager in app context
        app.db_manager = db_manager
    
    return db_manager
