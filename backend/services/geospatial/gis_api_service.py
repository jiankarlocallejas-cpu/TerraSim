"""
GIS API Service - FastAPI endpoints for geospatial operations.
RESTful interface to the GIS engine.
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import tempfile
from pathlib import Path

from .core import (
    TerraSIMGISEngine, Canvas, Layer, Extent, 
    RasterLayer, VectorLayer, PointCloudLayer,
    LayerType, CRS, ProcessingResult
)


logger = logging.getLogger(__name__)

# Global GIS engine instance
_gis_engine: Optional[TerraSIMGISEngine] = None

def get_gis_engine() -> TerraSIMGISEngine:
    """Get or create GIS engine."""
    global _gis_engine
    if _gis_engine is None:
        _gis_engine = TerraSIMGISEngine("TerraSim GIS Service")
    return _gis_engine


# Request/Response Models
class CreateCanvasRequest(BaseModel):
    """Create canvas request."""
    name: str = Field(..., min_length=1)
    crs: str = "EPSG:4326"


class CanvasResponse(BaseModel):
    """Canvas response."""
    id: str
    name: str
    crs: str
    layer_count: int
    extent: Optional[Dict[str, float]]


class LayerResponse(BaseModel):
    """Layer response."""
    id: str
    name: str
    type: str
    crs: str
    visible: bool
    opacity: float
    extent: Optional[Dict[str, float]]
    status: str
    feature_count: int


class LoadLayerRequest(BaseModel):
    """Load layer request."""
    source: str = Field(..., description="File path or URL")
    name: Optional[str] = None
    canvas_id: Optional[str] = None


class SetLayerVisibilityRequest(BaseModel):
    """Set layer visibility."""
    layer_id: str
    visible: bool
    canvas_id: Optional[str] = None


class SetCanvasExtentRequest(BaseModel):
    """Set canvas extent."""
    xmin: float
    ymin: float
    xmax: float
    ymax: float
    zmin: float = 0.0
    zmax: float = 0.0
    canvas_id: Optional[str] = None


class ProcessingParametersRequest(BaseModel):
    """Processing algorithm parameters."""
    parameters: Dict[str, Any] = Field(default_factory=dict)


class CRSConversionRequest(BaseModel):
    """CRS conversion request."""
    x: float
    y: float
    source_crs: str
    target_crs: str


class ErosionAnalysisRequest(BaseModel):
    """Erosion analysis request."""
    dem_before_id: str
    dem_after_id: str
    cell_size: float = 1.0
    canvas_id: Optional[str] = None


# Create router
router = APIRouter(prefix="/api/gis", tags=["GIS"])


# Canvas Endpoints
@router.post("/canvases", response_model=CanvasResponse)
def create_canvas(request: CreateCanvasRequest, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Create new map canvas."""
    try:
        canvas = engine.create_canvas(request.name, request.crs)
        return CanvasResponse(
            id=canvas.id,
            name=canvas.name,
            crs=canvas.crs,
            layer_count=canvas.get_layer_count(),
            extent=canvas.extent.to_dict() if canvas.extent else None
        )
    except Exception as e:
        logger.error(f"Error creating canvas: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/canvases/{canvas_id}", response_model=CanvasResponse)
def get_canvas(canvas_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Get canvas details."""
    canvas = engine.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    return CanvasResponse(
        id=canvas.id,
        name=canvas.name,
        crs=canvas.crs,
        layer_count=canvas.get_layer_count(),
        extent=canvas.extent.to_dict() if canvas.extent else None
    )


@router.get("/canvases")
def list_canvases(engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """List all canvases."""
    canvases = engine.get_canvases()
    return {
        'canvases': [
            {
                'id': c.id,
                'name': c.name,
                'crs': c.crs,
                'layer_count': c.get_layer_count()
            }
            for c in canvases
        ]
    }


@router.post("/canvases/{canvas_id}/active")
def set_active_canvas(canvas_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Set active canvas."""
    if engine.set_active_canvas(canvas_id):
        return {'status': 'success', 'canvas_id': canvas_id}
    raise HTTPException(status_code=404, detail="Canvas not found")


@router.delete("/canvases/{canvas_id}")
def delete_canvas(canvas_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Delete canvas."""
    if engine.delete_canvas(canvas_id):
        return {'status': 'success'}
    raise HTTPException(status_code=404, detail="Canvas not found")


# Layer Endpoints
@router.post("/layers/load")
def load_layer(request: LoadLayerRequest, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Load layer from file."""
    try:
        layer = engine.load_layer(request.source, request.name)
        if not layer:
            raise HTTPException(status_code=400, detail="Failed to load layer")
        
        if request.canvas_id:
            engine.set_active_canvas(request.canvas_id)
        
        return {
            'layer_id': layer.id,
            'name': layer.name,
            'type': layer.layer_type.value,
            'feature_count': layer.get_feature_count()
        }
    except Exception as e:
        logger.error(f"Error loading layer: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/{layer_id}", response_model=LayerResponse)
def get_layer(layer_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Get layer details."""
    layer = engine.get_layer(layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    
    return LayerResponse(
        id=layer.id,
        name=layer.name,
        type=layer.layer_type.value,
        crs=layer.crs,
        visible=layer.is_visible,
        opacity=layer.opacity,
        extent=layer.extent.to_dict() if layer.extent else None,
        status=layer.status,
        feature_count=layer.get_feature_count()
    )


@router.get("/layers")
def list_layers(
    canvas_id: Optional[str] = None,
    layer_type: Optional[str] = None,
    engine: TerraSIMGISEngine = Depends(get_gis_engine)
):
    """List layers in canvas."""
    layers = engine.get_layers(canvas_id)
    
    # Filter by type if specified
    if layer_type:
        layers = [l for l in layers if l.layer_type.value == layer_type]
    
    return {
        'layers': [
            {
                'id': layer.id,
                'name': layer.name,
                'type': layer.layer_type.value,
                'visible': layer.is_visible,
                'opacity': layer.opacity
            }
            for layer in layers
        ],
        'count': len(layers)
    }


@router.post("/layers/{layer_id}/visibility")
def set_layer_visibility(layer_id: str, request: SetLayerVisibilityRequest,
                        engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Set layer visibility."""
    canvas_id = request.canvas_id
    canvas = engine.get_canvas(canvas_id) if canvas_id else engine.get_active_canvas()
    
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    if canvas.set_layer_visibility(layer_id, request.visible):
        return {'status': 'success', 'layer_id': layer_id, 'visible': request.visible}
    
    raise HTTPException(status_code=404, detail="Layer not found")


@router.post("/layers/{layer_id}/opacity")
def set_layer_opacity(layer_id: str, opacity: float = Query(..., ge=0.0, le=1.0),
                     engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Set layer opacity."""
    layer = engine.get_layer(layer_id)
    if not layer:
        raise HTTPException(status_code=404, detail="Layer not found")
    
    layer.opacity = opacity
    return {'status': 'success', 'layer_id': layer_id, 'opacity': opacity}


@router.post("/layers/{layer_id}/save")
def save_layer(layer_id: str, destination: str = Query(...),
              engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Save layer to file."""
    if engine.save_layer(layer_id, destination):
        return {'status': 'success', 'destination': destination}
    
    raise HTTPException(status_code=400, detail="Failed to save layer")


@router.delete("/layers/{layer_id}")
def delete_layer(layer_id: str, canvas_id: Optional[str] = None,
                engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Delete layer from canvas."""
    if engine.remove_layer(layer_id, canvas_id):
        return {'status': 'success'}
    
    raise HTTPException(status_code=404, detail="Layer not found")


@router.get("/layers/{layer_id}/statistics")
def get_layer_statistics(layer_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Get layer statistics."""
    stats = engine.calculate_layer_statistics(layer_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Layer not found")
    
    return stats


# Canvas Navigation Endpoints
@router.post("/canvases/{canvas_id}/extent")
def set_canvas_extent(canvas_id: str, request: SetCanvasExtentRequest,
                     engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Set canvas extent."""
    canvas = engine.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    extent = Extent(
        xmin=request.xmin,
        ymin=request.ymin,
        xmax=request.xmax,
        ymax=request.ymax,
        zmin=request.zmin,
        zmax=request.zmax
    )
    
    canvas.zoom_to_extent(extent)
    return {'status': 'success', 'extent': extent.to_dict()}


@router.post("/canvases/{canvas_id}/zoom-to-layer/{layer_id}")
def zoom_to_layer(canvas_id: str, layer_id: str,
                 engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Zoom canvas to layer extent."""
    canvas = engine.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    if canvas.zoom_to_layer(layer_id):
        return {'status': 'success'}
    
    raise HTTPException(status_code=404, detail="Layer not found")


@router.post("/canvases/{canvas_id}/zoom-to-all")
def zoom_to_all_layers(canvas_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Zoom canvas to fit all layers."""
    canvas = engine.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    canvas.zoom_to_all_layers()
    return {'status': 'success', 'extent': canvas.extent.to_dict()}


@router.post("/canvases/{canvas_id}/zoom")
def zoom_canvas(canvas_id: str, factor: float = Query(...),
               engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Zoom canvas in/out."""
    canvas = engine.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    canvas.zoom(factor)
    return {'status': 'success', 'extent': canvas.extent.to_dict()}


# CRS Endpoints
@router.post("/crs/transform")
def transform_coordinates(request: CRSConversionRequest,
                         engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Transform coordinates between CRS."""
    transformer = engine.create_coordinate_transformer(request.source_crs, request.target_crs)
    if not transformer:
        raise HTTPException(status_code=400, detail="Invalid CRS")
    
    x_out, y_out = transformer.transform_point(request.x, request.y)
    return {
        'source_crs': request.source_crs,
        'target_crs': request.target_crs,
        'source': {'x': request.x, 'y': request.y},
        'target': {'x': x_out, 'y': y_out}
    }


# Processing Endpoints
@router.get("/processing/algorithms")
def list_algorithms(engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """List available processing algorithms."""
    return engine.get_processing_algorithms()


@router.post("/processing/run/{algorithm_id}")
def run_algorithm(algorithm_id: str, request: ProcessingParametersRequest,
                 engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Run processing algorithm."""
    try:
        result = engine.run_algorithm(algorithm_id, request.parameters)
        if not result:
            raise HTTPException(status_code=404, detail="Algorithm not found")
        
        return {
            'success': result.success,
            'processing_time': result.processing_time,
            'statistics': result.statistics,
            'error_message': result.error_message,
            'output_layers': [layer.id for layer in (result.output_layers.values() if result.output_layers else [])]
        }
    except Exception as e:
        logger.error(f"Error running algorithm: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Analysis Endpoints
@router.post("/analysis/dem-derivatives/{dem_id}")
def compute_dem_derivatives(dem_id: str, engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Compute DEM derivative layers."""
    try:
        derivatives = engine.compute_dem_derivatives(dem_id)
        if not derivatives:
            raise HTTPException(status_code=404, detail="DEM layer not found")
        
        return {
            'derivatives': {
                name: {
                    'layer_id': layer.id,
                    'name': layer.name
                }
                for name, layer in derivatives.items()
            }
        }
    except Exception as e:
        logger.error(f"Error computing derivatives: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/erosion")
def analyze_erosion(request: ErosionAnalysisRequest,
                   engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Analyze erosion between two DEMs."""
    try:
        stats = engine.analyze_erosion(
            request.dem_before_id,
            request.dem_after_id,
            request.cell_size
        )
        
        if not stats:
            raise HTTPException(status_code=404, detail="DEM layers not found")
        
        return stats
    except Exception as e:
        logger.error(f"Error analyzing erosion: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Status Endpoint
@router.get("/status")
def get_status(engine: TerraSIMGISEngine = Depends(get_gis_engine)):
    """Get GIS engine status."""
    return engine.get_status()
