import logging
from sqlalchemy.orm import Session

from core.config import settings
from .session import engine, Base
from models.user import User
from models.project import Project
from models.erosion_result import ErosionResult
from models.analysis_metrics import AnalysisMetrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db(db: Session) -> None:
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Create default admin user if not exists
    user = db.query(User).filter(User.email == settings.FIRST_SUPERUSER).first()
    if not user:
        from core.security import get_password_hash
        user = User(
            email=settings.FIRST_SUPERUSER,
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            full_name="Admin",
            is_superuser=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Default admin user created")

def reset_db() -> None:
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete")
