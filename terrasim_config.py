"""
TerraSim Professional Configuration
Customize settings for your erosion analysis application
"""

# ============================================================================
# UI Configuration
# ============================================================================

UI_CONFIG = {
    # Window settings
    "window": {
        "title": "TerraSim - Professional Erosion Analysis System",
        "default_width": 1600,
        "default_height": 1000,
        "resizable": True,
    },
    
    # Theme colors
    "colors": {
        "background": "#f0f0f0",
        "panel": "#e8e8e8",
        "accent": "#0078d4",
        "text": "#000000",
        "success": "#107c10",
        "warning": "#ffb900",
        "error": "#da3b01",
    },
    
    # Panel widths (pixels)
    "panels": {
        "layers_width": 300,
        "properties_width": 300,
    },
    
    # Default view
    "canvas": {
        "background_color": "white",
        "grid_enabled": True,
        "grid_alpha": 0.3,
    },
}

# ============================================================================
# Analysis Configuration
# ============================================================================

ANALYSIS_CONFIG = {
    # Erosion analysis methods
    "methods": {
        "M3C2": {
            "name": "Multiscale Model to Model Cloud Comparison",
            "description": "Standard point cloud differencing",
            "parameters": {
                "search_radius": {"default": 10.0, "min": 1.0, "max": 100.0, "step": 0.1},
                "max_normal_angle": {"default": 45, "min": 0, "max": 90, "step": 1},
            }
        },
        "ICP": {
            "name": "Iterative Closest Point",
            "description": "Registration-based differencing",
            "parameters": {
                "max_iterations": {"default": 50, "min": 10, "max": 1000, "step": 10},
                "convergence_threshold": {"default": 0.001, "min": 0.0001, "max": 0.1},
            }
        },
        "Point-to-Plane": {
            "name": "Point-to-Plane ICP",
            "description": "Surface-based registration",
            "parameters": {
                "max_iterations": {"default": 50, "min": 10, "max": 1000, "step": 10},
                "distance_threshold": {"default": 1.0, "min": 0.1, "max": 10.0, "step": 0.1},
            }
        },
    },
    
    # Change detection thresholds
    "thresholds": {
        "elevation_change": {"default": 0.1, "min": 0.01, "max": 10.0, "unit": "m"},
        "search_radius": {"default": 5.0, "min": 1.0, "max": 50.0, "unit": "m"},
        "confidence_level": {"default": 0.95, "min": 0.5, "max": 0.99, "unit": "confidence"},
    },
}

# ============================================================================
# Visualization Configuration
# ============================================================================

VISUALIZATION_CONFIG = {
    # Colormaps for different analysis types
    "colormaps": {
        "elevation": {
            "name": "Terrain",
            "colormap": "terrain",
            "description": "Standard terrain elevation coloring",
        },
        "change": {
            "name": "Change (Red-Blue)",
            "colormap": "RdBu_r",
            "description": "Red=deposition, Blue=erosion",
        },
        "magnitude": {
            "name": "Magnitude",
            "colormap": "viridis",
            "description": "Viridis colormap for magnitude visualization",
        },
        "slope": {
            "name": "Slope",
            "colormap": "hot",
            "description": "Hot colormap for slope visualization",
        },
    },
    
    # Default rendering modes
    "default_rendering": {
        "base_dem": "elevation",
        "erosion_result": "erosion_deposition",
        "difference_map": "change",
        "slope": "slope",
    },
    
    # Contour settings
    "contours": {
        "enabled": True,
        "interval": 10.0,  # meters
        "color": "#333333",
        "alpha": 0.5,
        "line_width": 0.5,
    },
    
    # Hillshade settings
    "hillshade": {
        "azimuth": 315,  # degrees
        "altitude": 45,   # degrees
        "z_factor": 1.0,  # vertical exaggeration
    },
}

# ============================================================================
# Data Import/Export Configuration
# ============================================================================

DATA_IO_CONFIG = {
    # Supported formats
    "formats": {
        "raster": ["GeoTIFF", "COG", "HGT", "ASCII Grid"],
        "vector": ["Shapefile", "GeoJSON", "GeoPackage", "KML"],
        "pointcloud": ["LAS", "LAZ", "E57", "PLY"],
    },
    
    # Export options
    "export": {
        "compression": "lzw",  # "lzw" or "deflate"
        "tiled": False,        # Create tiled GeoTIFF
        "blocksize": 256,      # Block size for tiled TIFFs
        "predictor": None,     # None, "horizontal", or "floating_point"
    },
    
    # Data quality settings
    "quality": {
        "validate_on_import": True,
        "elevation_min": -500,      # m
        "elevation_max": 9000,      # m
        "max_nodata_percentage": 50,  # %
    },
}

# ============================================================================
# Performance Configuration
# ============================================================================

PERFORMANCE_CONFIG = {
    # Processing
    "processing": {
        "max_threads": 4,
        "chunk_size": 1000,  # Process data in chunks
        "enable_caching": True,
    },
    
    # Rendering
    "rendering": {
        "max_texture_size": 4096,
        "decimation_threshold": 1000000,  # Points over this: apply decimation
        "decimation_factor": 0.5,
    },
    
    # Memory
    "memory": {
        "max_raster_size": 4294967296,  # 4 GB
        "lazy_loading": True,
    },
}

# ============================================================================
# Coordinate Reference System (CRS) Configuration
# ============================================================================

CRS_CONFIG = {
    # Default CRS
    "default_crs": "EPSG:4326",  # WGS84
    
    # Common CRS options
    "common_crs": {
        "WGS84": "EPSG:4326",
        "UTM": "EPSG:32633",  # UTM Zone 33N
        "Web Mercator": "EPSG:3857",
        "Equal Earth": "ESRI:54035",
    },
    
    # Unit preferences
    "units": {
        "horizontal": "meters",
        "vertical": "meters",
        "area": "square_meters",
        "volume": "cubic_meters",
    },
}

# ============================================================================
# Logging Configuration
# ============================================================================

LOGGING_CONFIG = {
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "date_format": "%Y-%m-%d %H:%M:%S",
    
    "handlers": {
        "console": {
            "enabled": True,
            "level": "INFO",
        },
        "file": {
            "enabled": True,
            "level": "DEBUG",
            "filename": "terrasim.log",
            "max_size_mb": 10,
            "backup_count": 5,
        },
    },
}

# ============================================================================
# Project Configuration
# ============================================================================

PROJECT_CONFIG = {
    # Default project settings
    "defaults": {
        "crs": "EPSG:4326",
        "unit": "meters",
        "cell_size": 1.0,
    },
    
    # Project file locations
    "paths": {
        "projects": "./projects",
        "data": "./data",
        "results": "./results",
        "cache": "./cache",
    },
    
    # Auto-save settings
    "autosave": {
        "enabled": True,
        "interval_seconds": 300,  # 5 minutes
    },
}

# ============================================================================
# Advanced Settings
# ============================================================================

ADVANCED_CONFIG = {
    # Feature flags
    "features": {
        "real_time_preview": True,
        "batch_processing": True,
        "plugin_system": False,
        "web_interface": False,
    },
    
    # Database (if using)
    "database": {
        "enabled": False,
        "driver": "sqlite",
        "url": "sqlite:///./terrasim.db",
    },
    
    # API Settings (if running backend server)
    "api": {
        "enabled": False,
        "host": "localhost",
        "port": 8000,
        "debug": False,
    },
}

# ============================================================================
# Helper Functions
# ============================================================================

def get_config(section: str, key: str | None = None, default=None):
    """Get configuration value"""
    config_map = {
        "ui": UI_CONFIG,
        "analysis": ANALYSIS_CONFIG,
        "visualization": VISUALIZATION_CONFIG,
        "data_io": DATA_IO_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "crs": CRS_CONFIG,
        "logging": LOGGING_CONFIG,
        "project": PROJECT_CONFIG,
        "advanced": ADVANCED_CONFIG,
    }
    
    config = config_map.get(section)
    if config is None:
        return default
    
    if key is None:
        return config
    
    return config.get(key, default)


def set_config(section: str, key: str, value):
    """Set configuration value"""
    config_map = {
        "ui": UI_CONFIG,
        "analysis": ANALYSIS_CONFIG,
        "visualization": VISUALIZATION_CONFIG,
        "data_io": DATA_IO_CONFIG,
        "performance": PERFORMANCE_CONFIG,
        "crs": CRS_CONFIG,
        "logging": LOGGING_CONFIG,
        "project": PROJECT_CONFIG,
        "advanced": ADVANCED_CONFIG,
    }
    
    config = config_map.get(section)
    if config is not None:
        config[key] = value


def print_config():
    """Print all configuration values"""
    print("\n" + "="*60)
    print("TerraSim Professional - Configuration Summary")
    print("="*60)
    
    sections = {
        "UI": UI_CONFIG,
        "Analysis": ANALYSIS_CONFIG,
        "Visualization": VISUALIZATION_CONFIG,
        "Data I/O": DATA_IO_CONFIG,
        "Performance": PERFORMANCE_CONFIG,
        "CRS": CRS_CONFIG,
        "Logging": LOGGING_CONFIG,
        "Project": PROJECT_CONFIG,
        "Advanced": ADVANCED_CONFIG,
    }
    
    for section_name, section_config in sections.items():
        print(f"\n{section_name}:")
        print("-" * 40)
        for key, value in section_config.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for k, v in value.items():
                    print(f"    {k}: {v}")
            else:
                print(f"  {key}: {value}")
    
    print("\n" + "="*60 + "\n")


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Print all configuration
    print_config()
    
    # Get specific values
    window_config = get_config("ui", "window")
    if window_config:
        print("Window title:", window_config.get("title", "N/A"))
    print("Default CRS:", get_config("crs", "default_crs"))
    
    # Modify configuration
    current_window = get_config("ui", "window")
    if current_window:
        set_config("ui", "window", {**current_window, "default_width": 1920})
        print("Updated window width to 1920")
