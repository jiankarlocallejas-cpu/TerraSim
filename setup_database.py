#!/usr/bin/env python
"""
Database initialization script for TerraSim.
Creates all tables and initializes the database with required schemas.

Usage:
    python setup_database.py
"""

import logging
import sys
from pathlib import Path

# Add backend to path
backend_path = str(Path(__file__).parent / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from backend.db.session import engine, SessionLocal
from backend.models.base import Base
from backend.models.user import User
from backend.models.project import Project
from backend.models.analysis import Analysis
from backend.models.erosion_result import ErosionResult
from backend.models.analysis_metrics import AnalysisMetrics
from backend.core.config import settings
from backend.core.security import get_password_hash

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)  # type: ignore
        logger.info("[OK] All database tables created successfully")
        return True
    except Exception as e:
        logger.error(f"[ERROR] Error creating tables: {e}")
        return False


def create_default_user():
    """Create default admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        logger.info("Checking for default admin user...")
        user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
        
        if user:
            logger.info(f"[OK] Default admin user already exists: {settings.FIRST_SUPERUSER}")
        else:
            logger.info(f"Creating default admin user: {settings.FIRST_SUPERUSER}")
            user = User(  # type: ignore[call-arg]
                email=settings.FIRST_SUPERUSER,  # type: ignore[arg-type]
                hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),  # type: ignore[arg-type]
                full_name="Administrator",  # type: ignore[arg-type]
                is_superuser=True,  # type: ignore[arg-type]
                is_active=True,  # type: ignore[arg-type]
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"[OK] Default admin user created: {user.email}")
        
        return True
    except Exception as e:
        logger.error(f"[ERROR] Error creating default user: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_models():
    """Verify all models are properly registered"""
    logger.info("Verifying database models...")
    models = {
        "User": User,
        "Project": Project,
        "Analysis": Analysis,
        "ErosionResult": ErosionResult,
        "AnalysisMetrics": AnalysisMetrics,
    }
    
    for name, model in models.items():
        logger.info(f"  [OK] {name} -> table: {model.__tablename__}")
    
    logger.info(f"[OK] All {len(models)} models verified")
    return True


def print_database_info():
    """Print database connection info"""
    logger.info("=" * 60)
    logger.info("Database Configuration")
    logger.info("=" * 60)
    logger.info(f"Database URL: {settings.DATABASE_URI}")
    logger.info(f"Admin Email: {settings.FIRST_SUPERUSER}")
    logger.info("=" * 60)


def main():
    """Main initialization sequence"""
    logger.info("Starting TerraSim Database Setup...")
    logger.info("=" * 60)
    
    # Print config
    print_database_info()
    
    # Create tables
    if not create_tables():
        logger.error("Failed to create tables")
        return False
    
    # Verify models
    if not verify_models():
        logger.error("Failed to verify models")
        return False
    
    # Create default user
    if not create_default_user():
        logger.error("Failed to create default user")
        return False
    
    logger.info("=" * 60)
    logger.info("[OK] Database setup completed successfully!")
    logger.info("=" * 60)
    logger.info("\nNext steps:")
    logger.info("1. Update .env file with your database credentials")
    logger.info("2. Start the backend: python backend/main.py")
    logger.info("3. Access API docs at http://localhost:8000/docs")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
