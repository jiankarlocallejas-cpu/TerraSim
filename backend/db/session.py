"""
Database session management and transaction handling for TerraSim.
Provides connection pooling, transaction management, and error handling.
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import SQLAlchemyError
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import settings
from core.exceptions import DatabaseError
from models.base import Base

logger = logging.getLogger(__name__)

# Create database engine with appropriate pool settings based on database type
db_url = str(settings.DATABASE_URI)

if db_url.startswith("sqlite"):
    # SQLite doesn't support connection pooling
    engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False,  # Set to True for SQL debugging
    )
    logger.info(f"SQLite database initialized: {db_url}")
else:
    # PostgreSQL with connection pooling
    engine = create_engine(
        db_url,
        pool_pre_ping=True,  # Verify connections are alive before using
        pool_size=getattr(settings, 'DATABASE_POOL_SIZE', 20),
        max_overflow=getattr(settings, 'DATABASE_MAX_OVERFLOW', 10),
        pool_recycle=3600,  # Recycle connections after 1 hour
        echo=False,  # Set to True for SQL debugging
    )
    logger.info(f"PostgreSQL database initialized: {db_url.split('@')[1] if '@' in db_url else 'configured'}")


@event.listens_for(engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Enable foreign key constraints for SQLite."""
    if db_url.startswith("sqlite"):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Only register pool_connect for SQLite (PostgreSQL connection pooling doesn't support this event)
if db_url.startswith("sqlite"):
    @event.listens_for(engine, "pool_connect")
    def receive_pool_connect(dbapi_conn, connection_record):
        """Log connection pool events."""
        logger.debug("Database connection established")


# Create a scoped session factory
SessionLocal = scoped_session(
    sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False
    )
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    Handles session cleanup and error management.
    
    Yields:
        SQLAlchemy Session instance
    
    Raises:
        DatabaseError: If session creation fails
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in session: {e}")
        raise DatabaseError(
            message="Database operation failed",
            query=str(e.statement) if hasattr(e, 'statement') else None,
            context={"error_type": type(e).__name__}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in database session: {e}")
        raise
    finally:
        db.close()


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database session with automatic cleanup.
    Use this for non-FastAPI code (e.g., background tasks, scripts).
    
    Yields:
        SQLAlchemy Session instance
    
    Raises:
        DatabaseError: If session operations fail
    
    Example:
        with get_db_session() as db:
            user = db.query(User).filter(User.id == 1).first()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error in context manager: {e}")
        raise DatabaseError(
            message="Database operation failed",
            query=str(e.statement) if hasattr(e, 'statement') else None,
            context={"error_type": type(e).__name__}
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in database context: {e}")
        raise
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.
    Creates all tables defined in models if they don't exist.
    """
    try:
        logger.info("Initializing database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except SQLAlchemyError as e:
        logger.error(f"Failed to initialize database: {e}")
        raise DatabaseError(
            message="Failed to initialize database tables",
            context={"error": str(e)}
        )


def drop_db() -> None:
    """
    Drop all database tables.
    WARNING: This is destructive and should only be used in development.
    """
    try:
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=engine)
        logger.warning("All database tables dropped")
    except SQLAlchemyError as e:
        logger.error(f"Failed to drop database tables: {e}")
        raise DatabaseError(
            message="Failed to drop database tables",
            context={"error": str(e)}
        )


def close_db() -> None:
    """Close all database connections in the session pool."""
    try:
        SessionLocal.remove()
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
        raise
