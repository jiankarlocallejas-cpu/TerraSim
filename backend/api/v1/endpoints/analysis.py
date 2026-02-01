from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import sys
from pathlib import Path
import numpy as np

# Add backend directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from db.session import get_db
from schemas.analysis import AnalysisCreate, AnalysisResult, ErosionAnalysisParameters, ErosionAnalysisResults
from services.geospatial.analysis import (
    create_analysis,
    get_analyses,
    get_analysis,
    run_analysis,
    CorrelationAnalysis,
    RegressionAnalysis,
    ModelValidation,
    UncertaintyQuantification
)
from services.erosion_model import (
    TerraSIMErosionModel,
    RainfallRunoffCalculator,
    SoilErodibilityCalculator,
    SoilModelParameters,
    ErosionFactors
)
from services.geospatial import DEMProcessor, LandCoverProcessor, SoilDataProcessor
from api.deps import get_current_active_user
from schemas.user import User

router = APIRouter()


@router.post("/", response_model=AnalysisResult)
def create_new_analysis(
    analysis_in: AnalysisCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create and run a new analysis
    """
    analysis = create_analysis(db=db, analysis=analysis_in, owner_id=current_user.id)
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis.id,
        db=db
    )
    
    return analysis


@router.post("/erosion", response_model=AnalysisResult)
def create_erosion_analysis(
    params: ErosionAnalysisParameters,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Create a new erosion analysis
    """
    analysis_data = AnalysisCreate(
        name=f"Erosion Analysis - Point Cloud {params.pointcloud_id}",
        description="Erosion analysis using M3C2 algorithm",
        type="erosion",
        parameters=params.dict(),
        project_id=1  # This should come from the point cloud's project
    )
    
    analysis = create_analysis(db=db, analysis=analysis_data, owner_id=current_user.id)
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis.id,
        db=db
    )
    
    return analysis


@router.get("/", response_model=List[AnalysisResult])
def list_analyses(
    skip: int = 0, 
    limit: int = 100,
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    List all analyses for the current user
    """
    analyses = get_analyses(db, owner_id=current_user.id, skip=skip, limit=limit)
    
    # Filter by project if specified
    if project_id is not None:
        analyses = [a for a in analyses if a.project_id == project_id]
    
    return analyses


@router.get("/{analysis_id}", response_model=AnalysisResult)
def get_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get analysis by ID
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return analysis


@router.get("/{analysis_id}/results")
def get_analysis_results(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Get detailed analysis results
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    if analysis.status != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    return {
        "analysis_id": analysis_id,
        "results": analysis.results,
        "parameters": analysis.parameters
    }


@router.post("/{analysis_id}/rerun")
def rerun_analysis(
    analysis_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Rerun an analysis
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    # Reset status and run again
    from services.geospatial.analysis import update_analysis
    update_analysis(db, analysis_id, {"status": "pending", "results": {}})
    
    # Run analysis in background
    background_tasks.add_task(
        run_analysis,
        analysis_id=analysis.id,
        db=db
    )
    
    return {"message": "Analysis rerun started"}


@router.post("/erosion-simulation", response_model=Dict[str, Any])
async def run_erosion_simulation(
    parameters: ErosionAnalysisParameters,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Run TerraSim erosion simulation with USPED-based model.
    
    Implements the 2.5D SoilModel framework with:
    - Rainfall-runoff computation (SCS-CN method)
    - Sediment transport calculation
    - Erosion-deposition prediction
    - RUSLE comparison
    """
    try:
        # Initialize model components
        model = TerraSIMErosionModel(SoilModelParameters())
        rainfall_calc = RainfallRunoffCalculator()
        soil_calc = SoilErodibilityCalculator()
        
        # Compute rainfall erosivity
        R = rainfall_calc.compute_rainfall_erosivity(
            parameters.annual_rainfall,
            parameters.max_daily_rainfall
        )
        
        # Compute runoff using SCS-CN method
        CN = rainfall_calc.get_curve_number(
            parameters.land_use,
            parameters.soil_group
        )
        Q = rainfall_calc.compute_runoff(parameters.annual_rainfall, CN)
        
        # Compute soil erodibility
        K = soil_calc.compute_K_factor(
            parameters.sand_percent,
            parameters.silt_percent,
            parameters.clay_percent,
            parameters.organic_matter_percent
        )
        
        # Create erosion factors
        slope_rad = np.radians(parameters.slope)
        factors = ErosionFactors(
            R=R,
            K=K,
            C=parameters.C_factor,
            P=parameters.P_factor,
            LS=parameters.LS_factor,
            A=parameters.contributing_area,
            beta=slope_rad,
            Q=Q
        )
        
        # Compute sediment transport
        T = model.compute_sediment_transport(factors)
        
        # Compute RUSLE
        rusle_result = model.compute_rusle_comparison(factors)
        
        # Classify risk
        annual_soil_loss = rusle_result['annual_soil_loss_Mg_ha']
        risk_class = model.classify_erosion_risk(annual_soil_loss)
        
        # Store analysis result
        analysis = create_analysis(
            db=db,
            analysis=parameters,
            owner_id=current_user.id
        )
        
        result = {
            'analysis_id': analysis.id,
            'sediment_transport': float(T),
            'rainfall_erosivity_R': R,
            'soil_erodibility_K': K,
            'runoff_depth_mm': Q,
            'curve_number': CN,
            'rusle_results': rusle_result,
            'risk_classification': risk_class,
            'status': 'completed'
        }
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")


@router.post("/rusle-comparison", response_model=Dict[str, Any])
async def compare_with_rusle(
    terrasim_values: List[float],
    rusle_values: List[float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Compare TerraSim predictions with RUSLE results for validation.
    
    Tests hypothesis Ha1: TerraSim predictions are consistent with RUSLE
    """
    try:
        validator = ModelValidation()
        
        # Convert to numpy arrays
        ts_vals = np.array(terrasim_values)
        rusle_vals = np.array(rusle_values)
        
        # Perform comparison
        comparison = validator.compare_with_rusle(ts_vals, rusle_vals)
        
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")


@router.post("/correlation-analysis", response_model=Dict[str, Any])
async def analyze_factor_correlations(
    factors: Dict[str, List[float]],
    erosion_values: List[float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Analyze correlations between environmental factors and erosion.
    
    Computes Pearson correlation coefficients and significance tests.
    """
    try:
        analyzer = CorrelationAnalysis()
        
        # Convert to numpy arrays
        erosion_arr = np.array(erosion_values)
        factor_arrays = {name: np.array(vals) for name, vals in factors.items()}
        
        # Perform correlation analysis
        results = analyzer.analyze_factor_relationships(factor_arrays, erosion_arr)
        
        return {
            'correlations': results,
            'n_samples': len(erosion_arr),
            'analysis_date': '2026-01-24'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@router.post("/uncertainty-analysis", response_model=Dict[str, Any])
async def analyze_uncertainty(
    erosion_values: List[float],
    rainfall_scenarios: Dict[str, float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Perform Value at Risk (VaR) and Conditional Value at Risk (CVaR) analysis.
    
    Identifies extreme erosion events under high-rainfall scenarios.
    """
    try:
        quantifier = UncertaintyQuantification()
        
        erosion_arr = np.array(erosion_values)
        
        # Compute VaR/CVaR at different confidence levels
        var_95 = quantifier.compute_var_cvar(erosion_arr, 0.95)
        var_99 = quantifier.compute_var_cvar(erosion_arr, 0.99)
        
        return {
            'var_95_percent': var_95,
            'var_99_percent': var_99,
            'rainfall_scenarios': rainfall_scenarios,
            'interpretation': 'Erosion risk analysis under extreme conditions'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Uncertainty analysis error: {str(e)}")


@router.post("/sensitivity-analysis", response_model=Dict[str, Any])
async def analyze_sensitivity(
    base_parameters: Dict[str, float],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis to identify critical parameters.
    
    Identifies which environmental factors have the greatest impact on erosion.
    """
    try:
        quantifier = UncertaintyQuantification()
        model = TerraSIMErosionModel(SoilModelParameters())
        
        # Define erosion function
        def erosion_function(params):
            slope_rad = np.radians(params.get('slope', 15))
            factors = ErosionFactors(
                R=params.get('R', 100),
                K=params.get('K', 0.2),
                C=params.get('C', 0.3),
                P=params.get('P', 1.0),
                LS=params.get('LS', 2.0),
                A=params.get('A', 1000),
                beta=slope_rad,
                Q=params.get('Q', 50)
            )
            return model.compute_sediment_transport(factors)
        
        # Perform sensitivity analysis
        sensitivity = quantifier.sensitivity_analysis(base_parameters, erosion_function)
        
        return {
            'sensitivity_results': sensitivity,
            'interpretation': 'Parameter sensitivity indices (higher = more sensitive)'
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sensitivity analysis error: {str(e)}")


@router.delete("/{analysis_id}")
def delete_analysis_by_id(
    analysis_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Delete analysis
    """
    analysis = get_analysis(db, analysis_id=analysis_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    from services.geospatial.analysis import delete_analysis
    success = delete_analysis(db, analysis_id=analysis_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete analysis")
    return {"message": "Analysis deleted successfully"}
