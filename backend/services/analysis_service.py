import os
import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import sys
from pathlib import Path

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.analysis import Analysis
from schemas.analysis import AnalysisCreate, AnalysisUpdate

logger = logging.getLogger(__name__)


def get_analysis(db: Session, analysis_id: int) -> Optional[Analysis]:
    """Get an analysis by ID"""
    return db.query(Analysis).filter(Analysis.id == analysis_id).first()


def get_analyses(db: Session, owner_id: int, skip: int = 0, limit: int = 100) -> List[Analysis]:
    """Get a list of analyses for a specific owner"""
    return (
        db.query(Analysis)
        .filter(Analysis.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def create_analysis(db: Session, analysis: AnalysisCreate, owner_id: int) -> Analysis:
    """Create a new analysis"""
    db_analysis = Analysis(
        name=analysis.name,
        description=analysis.description,
        type=analysis.type,
        parameters=analysis.parameters,
        project_id=analysis.project_id,
        owner_id=owner_id,
    )
    db.add(db_analysis)
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def update_analysis(db: Session, analysis_id: int, analysis: AnalysisUpdate) -> Optional[Analysis]:
    """Update an analysis"""
    db_analysis = get_analysis(db, analysis_id=analysis_id)
    if not db_analysis:
        return None
    
    update_data = analysis.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_analysis, field, value)
    
    db.commit()
    db.refresh(db_analysis)
    return db_analysis


def delete_analysis(db: Session, analysis_id: int) -> bool:
    """Delete an analysis"""
    db_analysis = get_analysis(db, analysis_id=analysis_id)
    if not db_analysis:
        return False
    
    db.delete(db_analysis)
    db.commit()
    return True


async def run_analysis(analysis_id: int, db: Session) -> Dict[str, Any]:
    """Run an analysis"""
    analysis = get_analysis(db, analysis_id)
    if not analysis:
        raise ValueError(f"Analysis {analysis_id} not found")
    
    try:
        # Update status to running
        update_analysis(db, analysis_id, AnalysisUpdate(status="running"))
        
        # Run the analysis based on type
        if analysis.type == "erosion":
            result = await run_erosion_analysis(analysis)
        elif analysis.type == "sediment":
            result = await run_sediment_analysis(analysis)
        else:
            raise ValueError(f"Unknown analysis type: {analysis.type}")
        
        # Update with results
        update_analysis(db, analysis_id, AnalysisUpdate(
            status="completed",
            results=result
        ))
        
        return result
        
    except Exception as e:
        logger.error(f"Error running analysis {analysis_id}: {str(e)}")
        update_analysis(db, analysis_id, AnalysisUpdate(
            status="failed",
            results={"error": str(e)}
        ))
        raise


async def run_erosion_analysis(analysis: Analysis) -> Dict[str, Any]:
    """Run erosion analysis"""
    parameters = analysis.parameters
    
    # This is a placeholder for actual erosion analysis
    # In a real implementation, this would:
    # 1. Load point cloud data
    # 2. Perform M3C2 or other differencing algorithms
    # 3. Calculate erosion/deposition volumes
    # 4. Generate visualizations
    
    result = {
        "total_volume_change": 0.0,
        "mean_elevation_change": 0.0,
        "std_elevation_change": 0.0,
        "positive_volume": 0.0,  # deposition
        "negative_volume": 0.0,  # erosion
        "area_analyzed": 0.0,
        "method": parameters.get("method", "m3c2"),
        "message": "Erosion analysis completed"
    }
    
    return result


async def run_sediment_analysis(analysis: Analysis) -> Dict[str, Any]:
    """Run sediment analysis"""
    parameters = analysis.parameters
    
    # This is a placeholder for actual sediment analysis
    # In a real implementation, this would:
    # 1. Load sediment data
    # 2. Calculate sediment transport
    # 3. Model sediment deposition patterns
    
    result = {
        "sediment_volume": 0.0,
        "transport_rate": 0.0,
        "deposition_areas": [],
        "erosion_areas": [],
        "message": "Sediment analysis completed"
    }
    
    return result
