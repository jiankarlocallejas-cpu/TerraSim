"""
Unified Data Service - Generic CRUD operations for rasters and point clouds
Consolidates common data management patterns for geospatial data types
"""

import os
import logging
from typing import List, Optional, Dict, Any, TypeVar, Generic, Type, cast
from sqlalchemy.orm import Session
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

T = TypeVar('T')  # Model type
C = TypeVar('C')  # Create schema type
U = TypeVar('U')  # Update schema type


class BaseDataService(ABC, Generic[T, C, U]):
    """Base service for CRUD operations on data models"""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def get_by_id(self, db: Session, item_id: int) -> Optional[T]:
        """Get item by ID"""
        return cast(Optional[T], db.query(self.model_class).filter(
            getattr(self.model_class, 'id') == item_id
        ).first())
    
    def get_by_owner(self, db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[T]:
        """Get items for a specific owner"""
        return cast(List[T], (
            db.query(self.model_class)
            .filter(getattr(self.model_class, 'owner_id') == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        ))
    
    def create(self, db: Session, item: C, owner_id: int, **kwargs) -> T:
        """Create new item - override in subclass for custom logic"""
        create_data = self._prepare_create_data(item, **kwargs)
        create_data['owner_id'] = owner_id
        db_item = self.model_class(**create_data)
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return cast(T, db_item)
    
    def update(self, db: Session, item_id: int, item: U) -> Optional[T]:
        """Update existing item"""
        db_item = self.get_by_id(db, item_id)
        if not db_item:
            return None
        
        if hasattr(item, 'dict'):
            update_data = cast(Any, item).dict(exclude_unset=True)
        else:
            update_data = {k: v for k, v in vars(item).items() if not k.startswith('_')}
        update_data = self._prepare_update_data(update_data)
        
        for field, value in update_data.items():
            setattr(db_item, field, value)
        
        db.commit()
        db.refresh(db_item)
        return cast(T, db_item)
    
    def delete(self, db: Session, item_id: int) -> bool:
        """Delete item"""
        db_item = self.get_by_id(db, item_id)
        if not db_item:
            return False
        
        # Delete associated file if it exists
        file_path = getattr(db_item, 'file_path', None)
        if file_path and isinstance(file_path, str):
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as e:
                    logger.warning(f"Could not delete file {file_path}: {e}")
        
        db.delete(db_item)
        db.commit()
        return True
    
    @abstractmethod
    def _prepare_create_data(self, item: C, **kwargs) -> Dict[str, Any]:
        """Prepare data for creation - implement in subclass"""
        pass
    
    @abstractmethod
    def _prepare_update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for update - implement in subclass"""
        pass
