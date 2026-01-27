"""
Terrain Simulation API Endpoints
REST API for time-stepped terrain simulation (World Machine-like evolution)
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
import logging

from backend.db.session import get_db
from backend.services.terrain_simulator import (
    TerrainSimulator,
    TimeStepParameters,
    SimulationMode,
    create_simulator_for_mode
)
from backend.core.exceptions import ValidationError, ProcessingError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/simulations", tags=["Terrain Simulation"])


# ==================== Pydantic Models ====================

class TimeStepParametersRequest(BaseModel):
    """Request model for simulation parameters"""
    dt: float = Field(1.0, ge=0.01, description="Time step in years")
    num_timesteps: int = Field(100, ge=1, le=10000, description="Number of timesteps")
    rho_b: float = Field(1300.0, gt=0, description="Bulk density (kg/m³)")
    epsilon: float = Field(0.01, ge=0, le=1, description="Vertical transport coefficient")
    m_exponent: float = Field(0.6, description="Flow accumulation exponent")
    n_exponent: float = Field(1.3, description="Slope exponent")
    rainfall_factor: float = Field(270.0, ge=0, description="R factor (MJ·mm/ha/yr)")
    damping_factor: float = Field(0.95, ge=0.5, le=1.0, description="Stability damping factor")
    
    class Config:
        schema_extra = {
            "example": {
                "dt": 1.0,
                "num_timesteps": 100,
                "rho_b": 1300.0,
                "epsilon": 0.01,
                "m_exponent": 0.6,
                "n_exponent": 1.3,
                "rainfall_factor": 270.0,
                "damping_factor": 0.95
            }
        }


class SimulationSnapshotResponse(BaseModel):
    """Response model for simulation snapshot"""
    timestep: int = Field(description="Timestep number")
    time_years: float = Field(description="Simulated time in years")
    max_elevation: float = Field(description="Maximum elevation (m)")
    min_elevation: float = Field(description="Minimum elevation (m)")
    mean_elevation: float = Field(description="Mean elevation (m)")
    total_volume_change: float = Field(description="Total volume change (m³)")
    
    class Config:
        schema_extra = {
            "example": {
                "timestep": 0,
                "time_years": 0.0,
                "max_elevation": 1500.5,
                "min_elevation": 100.2,
                "mean_elevation": 750.0,
                "total_volume_change": -1000000.0
            }
        }


class SimulationRequest(BaseModel):
    """Request model for starting a simulation"""
    mode: SimulationMode = Field(SimulationMode.MEDIUM, description="Simulation speed mode")
    dem_id: Optional[int] = Field(None, description="DEM raster ID from database")
    dem_data: Optional[List[List[float]]] = Field(None, description="DEM data as 2D array")
    cell_size: float = Field(10.0, gt=0, description="Grid cell size in meters")
    custom_params: Optional[TimeStepParametersRequest] = Field(None, description="Custom parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "mode": "medium",
                "dem_id": 1,
                "cell_size": 10.0,
                "custom_params": None
            }
        }


class SimulationResultResponse(BaseModel):
    """Response model for simulation results"""
    status: str = Field(description="Simulation status")
    total_timesteps: int = Field(description="Total timesteps completed")
    snapshots: List[SimulationSnapshotResponse] = Field(description="Snapshots at each timestep")
    start_elevation: float = Field(description="Initial mean elevation")
    end_elevation: float = Field(description="Final mean elevation")
    elevation_change: float = Field(description="Total elevation change")
    total_volume_change: float = Field(description="Total volume change")


# ==================== API Endpoints ====================

@router.post("/run", response_model=SimulationResultResponse, tags=["Terrain Simulation"])
async def run_terrain_simulation(
    request: SimulationRequest,
    db: Session = Depends(get_db),
    background_tasks: Optional[BackgroundTasks] = None
):
    """
    Run a time-stepped terrain simulation.
    
    Simulates terrain evolution over multiple timesteps using the elevation
    evolution equation. Supports different simulation modes:
    - **slow**: Geological timescale (thousands of years)
    - **medium**: Landscape evolution (hundreds of years)
    - **fast**: Rapid change (decades)
    - **extreme**: Severe events (years)
    
    The simulation shows how terrain changes dynamically through erosion
    and deposition processes, similar to World Machine.
    """
    try:
        logger.info(f"Starting terrain simulation with mode: {request.mode}")
        
        # Get DEM data
        dem_data = None
        if request.dem_id:
            # Load from database
            from backend.models.raster import Raster
            raster = db.query(Raster).filter(Raster.id == request.dem_id).first()  # type: ignore
            if not raster:
                raise ValidationError("DEM not found", field="dem_id")
            try:
                import rasterio
                import numpy as np
                with rasterio.open(raster.file_path) as src:
                    dem_data = src.read(1).astype(np.float64)
            except Exception as e:
                raise ValidationError(f"Failed to load DEM: {str(e)}", field="dem_id")
        elif request.dem_data:
            import numpy as np
            dem_data = np.array(request.dem_data, dtype=np.float64)
        else:
            raise ValidationError("Either dem_id or dem_data must be provided")
        
        # Create simulator and parameters
        if request.custom_params:
            simulator = TerrainSimulator(dem_data, request.cell_size)
            params = TimeStepParameters(
                dt=request.custom_params.dt,
                num_timesteps=request.custom_params.num_timesteps,
                rho_b=request.custom_params.rho_b,
                epsilon=request.custom_params.epsilon,
                m_exponent=request.custom_params.m_exponent,
                n_exponent=request.custom_params.n_exponent,
                rainfall_factor=request.custom_params.rainfall_factor,
                damping_factor=request.custom_params.damping_factor
            )
        else:
            simulator, params = create_simulator_for_mode(dem_data, request.mode, request.cell_size)
        
        # Run simulation
        snapshots = simulator.run_simulation(params)
        
        # Prepare response
        snapshot_responses = [
            SimulationSnapshotResponse(
                timestep=s.timestep,
                time_years=s.time_years,
                max_elevation=s.max_elevation,
                min_elevation=s.min_elevation,
                mean_elevation=s.mean_elevation,
                total_volume_change=s.total_volume_change
            )
            for s in snapshots
        ]
        
        # Calculate statistics
        start_elev = snapshots[0].mean_elevation if snapshots else 0
        end_elev = snapshots[-1].mean_elevation if snapshots else 0
        total_volume = snapshots[-1].total_volume_change if snapshots else 0
        
        result = SimulationResultResponse(
            status="completed",
            total_timesteps=len(snapshots),
            snapshots=snapshot_responses,
            start_elevation=start_elev,
            end_elevation=end_elev,
            elevation_change=end_elev - start_elev,
            total_volume_change=total_volume
        )
        
        logger.info(f"Simulation completed: {len(snapshots)} timesteps, "
                   f"elevation change: {result.elevation_change:.2f}m")
        
        return result
    
    except ValidationError as e:
        logger.error(f"Validation error in simulation: {e}")
        raise HTTPException(status_code=422, detail=str(e))
    except ProcessingError as e:
        logger.error(f"Processing error in simulation: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in simulation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Simulation failed")


@router.post("/quick", response_model=dict, tags=["Terrain Simulation"])
async def quick_simulation(
    mode: SimulationMode = SimulationMode.MEDIUM,
    dem_id: Optional[int] = None,
    cell_size: float = 10.0
):
    """
    Quick terrain simulation with preset parameters.
    
    Runs a simulation with standard parameters for the selected mode.
    Returns only final results without intermediate snapshots.
    """
    try:
        # This would load DEM from database
        # For now, return example structure
        return {
            "status": "quick_simulation_mode",
            "mode": mode,
            "message": "Use /run endpoint with dem_data for full simulation"
        }
    except Exception as e:
        logger.error(f"Quick simulation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modes", response_model=dict, tags=["Terrain Simulation"])
async def get_simulation_modes():
    """
    Get available simulation modes with descriptions.
    
    Returns information about each simulation mode:
    - Timescale
    - Duration
    - Intensity
    - Use cases
    """
    modes_info = {
        "slow": {
            "name": "Geological Timescale",
            "timestep_years": 10.0,
            "total_years": 1000.0,
            "intensity": "low",
            "description": "Slow geological processes over thousands of years",
            "use_cases": ["Long-term landscape evolution", "Mountain formation", "Deep weathering"]
        },
        "medium": {
            "name": "Landscape Evolution",
            "timestep_years": 5.0,
            "total_years": 1000.0,
            "intensity": "medium",
            "description": "Standard landscape evolution over hundreds of years",
            "use_cases": ["Valley formation", "River incision", "General erosion patterns"]
        },
        "fast": {
            "name": "Rapid Change",
            "timestep_years": 1.0,
            "total_years": 100.0,
            "intensity": "high",
            "description": "Rapid terrain changes over decades",
            "use_cases": ["Landslide regions", "Active gullying", "Severe erosion events"]
        },
        "extreme": {
            "name": "Severe Events",
            "timestep_years": 0.1,
            "total_years": 50.0,
            "intensity": "very_high",
            "description": "Extreme erosion from severe rainfall or floods",
            "use_cases": ["Flash flood erosion", "Storm damage", "Catastrophic events"]
        }
    }
    return modes_info


@router.post("/compare", response_model=dict, tags=["Terrain Simulation"])
async def compare_simulations(
    dem_data: List[List[float]],
    modes: Optional[List[SimulationMode]] = None,
    cell_size: float = 10.0
):
    """
    Compare multiple simulation modes on the same DEM.
    
    Runs simulations in different modes and compares results to show
    how different timescales affect terrain evolution.
    """
    try:
        if modes is None:
            modes = [SimulationMode.SLOW, SimulationMode.MEDIUM, SimulationMode.FAST]
        
        import numpy as np
        dem_array = np.array(dem_data, dtype=np.float64)
        
        results = {}
        for mode in modes:
            simulator, params = create_simulator_for_mode(dem_array, mode, cell_size)
            snapshots = simulator.run_simulation(params)
            
            final_snap = snapshots[-1]
            results[mode] = {
                "total_time_years": final_snap.time_years,
                "final_max_elevation": final_snap.max_elevation,
                "final_min_elevation": final_snap.min_elevation,
                "final_mean_elevation": final_snap.mean_elevation,
                "total_volume_change": final_snap.total_volume_change,
                "snapshots_count": len(snapshots)
            }
        
        return results
    
    except Exception as e:
        logger.error(f"Comparison error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Include in main API router
# from backend.api.v1.endpoints import terrain_simulation
# api_router.include_router(terrain_simulation.router)
