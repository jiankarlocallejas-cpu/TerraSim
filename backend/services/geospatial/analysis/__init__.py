"""
Analysis services for erosion modeling and statistical validation.

Provides:
- CRUD operations for analyses (analysis_crud)
- Statistical analysis and validation (statistics)

Components:
- analysis_crud: Database operations, analysis execution
- statistics: Correlation, regression, model validation, uncertainty quantification
"""

# CRUD Operations
from .analysis_crud import (
    get_analysis,
    get_analyses,
    create_analysis,
    update_analysis,
    delete_analysis,
    run_analysis,
    run_erosion_analysis,
    run_sediment_analysis,
    list_analysis_types,
    export_analysis_config,
    clone_analysis,
)

# Statistical Analysis
from .statistics import (
    CorrelationAnalysis,
    RegressionAnalysis,
    ModelValidation,
    UncertaintyQuantification,
)

__all__ = [
    # CRUD Operations
    'get_analysis',
    'get_analyses',
    'create_analysis',
    'update_analysis',
    'delete_analysis',
    'run_analysis',
    'run_erosion_analysis',
    'run_sediment_analysis',
    'list_analysis_types',
    'export_analysis_config',
    'clone_analysis',
    
    # Statistical Analysis Classes
    'CorrelationAnalysis',
    'RegressionAnalysis',
    'ModelValidation',
    'UncertaintyQuantification',
]
