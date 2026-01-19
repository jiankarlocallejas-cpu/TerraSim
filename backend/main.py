"""
TerraSim Backend Server
Advanced GIS Erosion Modeling Platform
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import rasterize
from shapely.geometry import Point, Polygon, LineString
import pyproj
from scipy import spatial
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="TerraSim API",
    description="Advanced GIS Erosion Modeling Platform",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="frontend/dist"), name="static")

# Pydantic Models
class ErosionInput(BaseModel):
    """Erosion model input parameters"""
    rainfall: float = Field(..., ge=0, description="Annual rainfall in mm")
    slope: float = Field(..., ge=0, le=90, description="Slope angle in degrees")
    slope_length: float = Field(..., ge=0, description="Slope length in meters")
    soil_type: str = Field(..., description="Soil type")
    vegetation_cover: float = Field(..., ge=0, le=100, description="Vegetation cover percentage")
    support_practices: float = Field(..., ge=0, le=100, description="Support practices percentage")
    land_use: str = Field(..., description="Land use type")
    area: float = Field(..., ge=0, description="Area in hectares")
    seasonality: str = Field(..., description="Seasonality type")

class GISData(BaseModel):
    """GIS data upload model"""
    data_type: str = Field(..., description="Type of GIS data")
    file_path: str = Field(..., description="File path")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Metadata")

class ErosionResult(BaseModel):
    """Erosion calculation result"""
    mean_loss: float
    peak_loss: float
    total_soil_loss: float
    confidence: float
    risk_category: str
    factors: Dict[str, float]
    rusle_comparison: Optional[Dict[str, float]] = None

# Core Erosion Engine
class ErosionEngine:
    """Advanced erosion modeling engine using Python GIS libraries"""
    
    def __init__(self):
        self.soil_factors = {
            'clay': 0.22,
            'sandy': 0.05,
            'loam': 0.29,
            'silt': 0.37,
            'rocky': 0.02
        }
        
        self.land_use_factors = {
            'forest': 0.001,
            'grassland': 0.01,
            'agriculture': 0.3,
            'urban': 0.5,
            'water': 0.0,
            'barren': 1.0
        }
        
        # Initialize ML model for advanced predictions
        self.ml_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.scaler = StandardScaler()
        self._train_model()
    
    def _train_model(self):
        """Train ML model with synthetic data"""
        # Generate training data
        n_samples = 1000
        X = np.random.rand(n_samples, 6)  # 6 features
        y = (X[:, 0] * 0.5 +  # rainfall factor
             X[:, 1] * 0.3 +  # slope factor
             X[:, 2] * 0.2 +  # soil factor
             X[:, 3] * 0.1 +  # vegetation factor
             X[:, 4] * 0.15 +  # land use factor
             X[:, 5] * 0.05) * 10  # area factor
        
        self.ml_model.fit(X, y)
        self.scaler.fit(X)
    
    def calculate_rusle(self, input_data: ErosionInput) -> float:
        """Calculate RUSLE soil loss"""
        # R factor - rainfall erosivity
        r_factor = 0.5 * (input_data.rainfall / 1000) * 100
        
        # K factor - soil erodibility
        k_factor = self.soil_factors.get(input_data.soil_type, 0.29)
        
        # LS factor - slope length and steepness
        slope_rad = np.radians(input_data.slope)
        slope_percent = np.tan(slope_rad) * 100
        
        m = 0.5
        if slope_percent < 1: m = 0.2
        elif slope_percent < 3: m = 0.3
        elif slope_percent < 5: m = 0.4
        
        length_factor = np.power(input_data.slope_length / 22.1, m)
        steepness_factor = 0.065 + 0.045 * slope_percent + 0.0065 * slope_percent**2
        ls_factor = length_factor * steepness_factor
        
        # C factor - cover management
        if input_data.vegetation_cover >= 80:
            c_factor = 0.001 + (100 - input_data.vegetation_cover) * 0.0004
        elif input_data.vegetation_cover >= 60:
            c_factor = 0.01 + (80 - input_data.vegetation_cover) * 0.0045
        elif input_data.vegetation_cover >= 20:
            c_factor = 0.1 + (60 - input_data.vegetation_cover) * 0.01
        else:
            c_factor = 0.5 + (20 - input_data.vegetation_cover) * 0.025
        
        # P factor - support practices
        if input_data.support_practices >= 75:
            p_factor = 0.1 + (100 - input_data.support_practices) * 0.006
        elif input_data.support_practices >= 50:
            p_factor = 0.25 + (75 - input_data.support_practices) * 0.01
        elif input_data.support_practices >= 25:
            p_factor = 0.5 + (50 - input_data.support_practices) * 0.01
        else:
            p_factor = 0.75 + (25 - input_data.support_practices) * 0.01
        
        # Calculate soil loss (tons/ha/year)
        soil_loss = r_factor * k_factor * ls_factor * c_factor * p_factor
        
        return soil_loss
    
    def calculate_terrak_sim(self, input_data: ErosionInput) -> ErosionResult:
        """Calculate TerraSim advanced erosion model"""
        
        # Calculate individual factors
        rainfall_factor = input_data.rainfall / 2000  # Normalized
        slope_factor = np.tan(np.radians(input_data.slope)) / 10
        soil_factor = self.soil_factors.get(input_data.soil_type, 0.29)
        vegetation_factor = (100 - input_data.vegetation_cover) / 100
        land_use_factor = self.land_use_factors.get(input_data.land_use, 0.3)
        
        # Seasonality factor
        season_factors = {'dry': 0.5, 'wet': 1.5, 'transitional': 1.0}
        seasonality_factor = season_factors.get(input_data.seasonality, 1.0)
        
        # ML-enhanced prediction
        features = np.array([[
            input_data.rainfall/2000,
            input_data.slope/90,
            soil_factor,
            vegetation_factor,
            land_use_factor,
            np.log(input_data.area + 1)
        ]])
        
        features_scaled = self.scaler.transform(features)
        ml_prediction = self.ml_model.predict(features_scaled)[0]
        
        # Calculate base erosion
        base_erosion = (rainfall_factor * slope_factor * soil_factor * 
                       vegetation_factor * land_use_factor * seasonality_factor)
        
        # Combine with ML prediction
        mean_loss = (base_erosion * 0.7 + ml_prediction * 0.3) * np.sqrt(input_data.area)
        peak_loss = mean_loss * (2.5 + np.random.random() * 0.5)
        total_soil_loss = mean_loss * input_data.area
        
        # Risk categorization
        if mean_loss < 2:
            risk_category = "Low"
        elif mean_loss < 5:
            risk_category = "Moderate"
        elif mean_loss < 10:
            risk_category = "High"
        else:
            risk_category = "Severe"
        
        # Confidence based on data quality
        confidence = min(0.95, 0.7 + (input_data.area / 100) * 0.25)
        
        # RUSLE comparison
        rusle_loss = self.calculate_rusle(input_data)
        rusle_comparison = {
            "soil_loss": rusle_loss,
            "difference": mean_loss - rusle_loss,
            "percent_difference": ((mean_loss - rusle_loss) / rusle_loss) * 100
        }
        
        return ErosionResult(
            mean_loss=mean_loss,
            peak_loss=peak_loss,
            total_soil_loss=total_soil_loss,
            confidence=confidence,
            risk_category=risk_category,
            factors={
                "rainfall_factor": rainfall_factor,
                "slope_factor": slope_factor,
                "soil_factor": soil_factor,
                "vegetation_factor": vegetation_factor,
                "land_use_factor": land_use_factor,
                "seasonality_factor": seasonality_factor
            },
            rusle_comparison=rusle_comparison
        )

# Initialize erosion engine
erosion_engine = ErosionEngine()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# API Routes
@app.get("/")
async def root():
    return {"message": "TerraSim API v2.0.0", "status": "running"}

@app.post("/api/erosion/calculate", response_model=ErosionResult)
async def calculate_erosion(input_data: ErosionInput):
    """Calculate erosion using TerraSim advanced model"""
    try:
        result = erosion_engine.calculate_terrak_sim(input_data)
        return result
    except Exception as e:
        logger.error(f"Erosion calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/erosion/rusle")
async def calculate_rusle_only(input_data: ErosionInput):
    """Calculate RUSLE soil loss only"""
    try:
        soil_loss = erosion_engine.calculate_rusle(input_data)
        return {"soil_loss": soil_loss, "model": "RUSLE"}
    except Exception as e:
        logger.error(f"RUSLE calculation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/gis/upload")
async def upload_gis_data(gis_data: GISData):
    """Upload and process GIS data"""
    try:
        # Process GIS data using GeoPandas and Rasterio
        if gis_data.data_type == "vector":
            # Process vector data
            gdf = gpd.read_file(gis_data.file_path)
            return {
                "status": "success",
                "features": len(gdf),
                "columns": list(gdf.columns),
                "crs": str(gdf.crs),
                "bounds": gdf.total_bounds.tolist()
            }
        elif gis_data.data_type == "raster":
            # Process raster data
            with rasterio.open(gis_data.file_path) as src:
                return {
                    "status": "success",
                    "width": src.width,
                    "height": src.height,
                    "bands": src.count,
                    "crs": str(src.crs),
                    "transform": list(src.transform)[:6],
                    "bounds": list(src.bounds)
                }
    except Exception as e:
        logger.error(f"GIS upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/gis/process/{data_type}")
async def process_gis_data(data_type: str):
    """Process GIS data for erosion analysis"""
    try:
        # Implement GIS processing logic
        return {"status": "processing", "data_type": data_type}
    except Exception as e:
        logger.error(f"GIS processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "dependencies": {
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "geopandas": gpd.__version__,
            "rasterio": rasterio.__version__
        }
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
