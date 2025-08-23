"""
Database models and utilities for SQLite integration
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, Float
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
    quality_metrics = Column(Text)  # JSON string of quality metrics
    
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
            'quality_metrics': json.loads(self.quality_metrics) if self.quality_metrics else {}
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
                    records: List[Dict[str, Any]], generation_metadata: Dict[str, Any] = None,
                    quality_metrics: Dict[str, Any] = None) -> int:
        """
        Save a complete dataset with records
        
        Args:
            name: Dataset name
            description: Dataset description
            schema_definition: Schema definition dictionary
            records: List of generated records
            generation_metadata: Generation metadata
            quality_metrics: Quality metrics
            
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
                quality_metrics=json.dumps(quality_metrics or {})
            )
            session.add(dataset)
            session.flush()  # Get the ID
            
            # Create data records
            for record in records:
                data_record = DataRecord(
                    dataset_id=dataset.id,
                    record_data=json.dumps(record.get('data', {})),
                    is_valid=record.get('is_valid', True),
                    validation_errors=json.dumps(record.get('validation_errors', [])),
                    generation_metadata=json.dumps(record.get('generation_metadata', {}))
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
