"""
TerraSim Modular API

Fast, modular terrain analysis using domain-based modules.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import Optional, List
import tempfile
from pathlib import Path
import numpy as np

from ..modules.manager import ModuleManager
from ..core.logging_config import logger

# Initialize modules
module_manager = ModuleManager()

app = FastAPI(
    title="TerraSim Modular API",
    description="Fast, modular terrain analysis",
    version="2.0.0"
)


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalysisRequest(BaseModel):
    """Analysis request parameters"""
    analysis_steps: int = 100
    description: Optional[str] = None


class ExportRequest(BaseModel):
    """Export request parameters"""
    format: str = 'json'  # json, csv, geotiff, html
    filename: Optional[str] = None


# ============================================================================
# Terrain Analysis Endpoints
# ============================================================================

@app.post("/api/v2/terrain/analyze")
async def analyze_terrain(file: UploadFile = File(...)):
    """Analyze terrain from DEM file"""
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Load and analyze
        dem, metadata = module_manager.data.load_dem(tmp_path)
        terrain_analysis = module_manager.terrain.analyze_dem(dem)
        
        return JSONResponse({
            'status': 'success',
            'metadata': metadata,
            'analysis': {
                'slope': {
                    'min': float(np.min(terrain_analysis['slope'])),
                    'max': float(np.max(terrain_analysis['slope'])),
                    'mean': float(np.mean(terrain_analysis['slope'])),
                },
                'aspect': {
                    'min': float(np.min(terrain_analysis['aspect'])),
                    'max': float(np.max(terrain_analysis['aspect'])),
                    'mean': float(np.mean(terrain_analysis['aspect'])),
                },
                'elevation': terrain_analysis['elevation_stats'],
            }
        })
    
    except Exception as e:
        logger.error(f"Terrain analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Cleanup
        if 'tmp_path' in locals():
            Path(tmp_path).unlink(missing_ok=True)


# ============================================================================
# Erosion Analysis Endpoints
# ============================================================================

@app.post("/api/v2/analysis/erosion")
async def run_erosion_analysis(
    file: UploadFile = File(...),
    request: AnalysisRequest = None,
    background_tasks: BackgroundTasks = None
):
    """Run erosion simulation"""
    try:
        if not request:
            request = AnalysisRequest()
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Load DEM
        dem, metadata = module_manager.data.load_dem(tmp_path)
        
        # Run erosion analysis
        results = module_manager.analysis.run_erosion_analysis(dem, request.analysis_steps)
        
        # Generate visualization
        viz = module_manager.visualization.create_visualization(
            results['final_dem'],
            title='Erosion Simulation'
        )
        
        return JSONResponse({
            'status': 'success',
            'metadata': metadata,
            'erosion_results': {
                'total_erosion': results['total_erosion'],
                'num_steps': len(results['steps']),
                'initial_elevation': float(np.mean(results['initial_dem'])),
                'final_elevation': float(np.mean(results['final_dem'])),
            },
            'visualization': viz,
        })
    
    except Exception as e:
        logger.error(f"Erosion analysis error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if 'tmp_path' in locals():
            Path(tmp_path).unlink(missing_ok=True)


# ============================================================================
# Visualization Endpoints
# ============================================================================

@app.post("/api/v2/visualization/heatmap")
async def create_heatmap(file: UploadFile = File(...)):
    """Create heatmap visualization from DEM"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        dem, _ = module_manager.data.load_dem(tmp_path)
        viz = module_manager.visualization.create_visualization(dem)
        
        return JSONResponse({
            'status': 'success',
            'visualization': viz,
        })
    
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if 'tmp_path' in locals():
            Path(tmp_path).unlink(missing_ok=True)


# ============================================================================
# Export Endpoints
# ============================================================================

@app.post("/api/v2/export/results")
async def export_results(
    file: UploadFile = File(...),
    format: str = 'json'
):
    """Export analysis results"""
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        dem, metadata = module_manager.data.load_dem(tmp_path)
        terrain_analysis = module_manager.terrain.analyze_dem(dem)
        erosion_results = module_manager.analysis.run_erosion_analysis(dem)
        
        results = {
            'metadata': metadata,
            'terrain_analysis': terrain_analysis,
            'erosion_results': erosion_results,
        }
        
        export_path = module_manager.export_analysis(results, format)
        
        return FileResponse(
            export_path,
            filename=export_path.name,
            media_type='application/octet-stream'
        )
    
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if 'tmp_path' in locals():
            Path(tmp_path).unlink(missing_ok=True)


# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/api/v2/status")
async def get_status():
    """Get API status and module info"""
    return JSONResponse({
        'status': 'healthy',
        'version': '2.0.0',
        'modules': {
            'terrain': 'active',
            'analysis': 'active',
            'data': 'active',
            'export': 'active',
            'visualization': 'active',
        },
    })


@app.get("/api/v2/health")
async def health_check():
    """Health check endpoint"""
    return {'status': 'ok'}


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
