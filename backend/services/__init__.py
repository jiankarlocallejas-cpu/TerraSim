"""Backend services with lazy legacy exports.

Importing a numerical or GIS submodule must not also load the historical API's
database, authentication, or point-cloud dependencies. The names previously
re-exported here remain available and are imported only when requested.
"""
from __future__ import annotations

from importlib import import_module
from typing import Any


_EXPORTS = {
    "SimulationEngine": ".simulation_engine",
    "get_simulation_engine": ".simulation_engine",
    **{
        name: ".user_service"
        for name in (
            "get_user",
            "get_user_by_email",
            "get_users",
            "create_user",
            "update_user",
            "delete_user",
            "authenticate_user",
            "is_active_user",
            "is_superuser",
        )
    },
    **{
        name: ".project_service"
        for name in (
            "get_project",
            "get_projects",
            "create_project",
            "update_project",
            "delete_project",
        )
    },
    **{
        name: ".geospatial.pointcloud_service"
        for name in (
            "get_pointcloud",
            "get_pointclouds",
            "create_pointcloud",
            "update_pointcloud",
            "delete_pointcloud",
            "process_pointcloud_file",
            "get_pointcloud_stats",
        )
    },
    **{
        name: ".geospatial.raster_service"
        for name in (
            "get_raster",
            "get_rasters",
            "create_raster",
            "update_raster",
            "delete_raster",
            "process_raster_file",
            "get_raster_stats",
            "create_cog",
        )
    },
    **{
        name: ".geospatial.analysis"
        for name in (
            "get_analysis",
            "get_analyses",
            "create_analysis",
            "update_analysis",
            "delete_analysis",
            "run_analysis",
        )
    },
    **{
        name: ".model_service"
        for name in (
            "get_model",
            "get_models",
            "create_model",
            "update_model",
            "delete_model",
            "train_model",
            "predict",
            "save_model",
            "load_model",
        )
    },
    **{
        name: ".job_service"
        for name in (
            "get_job",
            "get_jobs",
            "create_job",
            "update_job",
            "delete_job",
            "start_job",
            "complete_job",
            "fail_job",
            "cancel_job",
            "get_job_status",
            "update_job_progress",
            "append_job_log",
        )
    },
}

__all__ = list(_EXPORTS)


def __getattr__(name: str) -> Any:
    """Load an existing legacy service export only when its name is requested."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    value = getattr(import_module(module_name, __name__), name)
    globals()[name] = value
    return value

