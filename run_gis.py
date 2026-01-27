#!/usr/bin/env python3
"""
TerraSim GIS - Launcher Script
Starts the new GIS-style terrain simulation interface
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('terrasim_gis.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point"""
    try:
        logger.info("=" * 60)
        logger.info("Starting TerraSim GIS Interface")
        logger.info("=" * 60)
        
        # Check dependencies
        logger.info("Checking dependencies...")
        required_packages = [
            'numpy',
            'scipy',
            'matplotlib',
            'tkinter',
        ]
        
        optional_packages = [
            'geopandas',
            'rasterio',
            'shapely',
            'plotly',
            'moderngl',
        ]
        
        missing_required = []
        missing_optional = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✓ {package}")
            except ImportError:
                logger.error(f"✗ {package} (REQUIRED)")
                missing_required.append(package)
        
        for package in optional_packages:
            try:
                __import__(package)
                logger.info(f"✓ {package}")
            except ImportError:
                logger.warning(f"⚠ {package} (optional)")
                missing_optional.append(package)
        
        if missing_required:
            logger.error(f"Missing required packages: {', '.join(missing_required)}")
            logger.error("Please install: pip install -r requirements.txt")
            sys.exit(1)
        
        if missing_optional:
            logger.warning(f"Missing optional packages: {', '.join(missing_optional)}")
            logger.warning("Some features may be limited")
        
        logger.info("\n" + "=" * 60)
        logger.info("Initializing TerraSim GIS Interface...")
        logger.info("=" * 60 + "\n")
        
        # Import and run main application
        from frontend.main_gis import TerraSim_GIS
        
        app = TerraSim_GIS()
        logger.info("Application initialized successfully")
        logger.info("Starting main event loop...")
        
        app.mainloop()
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
