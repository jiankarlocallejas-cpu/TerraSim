"""
TerraSim - Main Entry Point
Launches backend API, tkinter GUI, and erosion calculation engine
"""

import subprocess
import sys
import time
import requests
from pathlib import Path
import threading
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """Verify all required dependencies are installed"""
    logger.info("Checking dependencies...")
    required_packages = [
        'geopandas', 'rasterio', 'shapely', 'numpy', 'scipy',
        'fastapi', 'sqlalchemy', 'pydantic'
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        logger.warning(f"Missing packages: {', '.join(missing)}")
        logger.info("Installing missing packages...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    
    logger.info("All dependencies available")
    return True

def initialize_database():
    """Initialize database if needed"""
    logger.info("Checking database...")
    db_path = Path("test.db")
    
    if not db_path.exists():
        logger.info("Initializing database tables...")
        try:
            from backend.db.session import engine
            from backend.models.base import BaseModel
            BaseModel.metadata.create_all(bind=engine)
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    else:
        logger.info("Database exists")
    
    return True

def start_backend():
    """Start the FastAPI backend server in a separate thread"""
    logger.info("Launching backend calculation engine...")
    try:
        subprocess.Popen(
            [sys.executable, "backend/main.py"],
            cwd=Path(__file__).parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info("Backend started (http://localhost:8000)")
        time.sleep(2)  # Give backend time to start
    except Exception as e:
        logger.error(f"Failed to start backend: {e}")
        return False
    return True

def start_calculation_engine():
    """Initialize the USPED erosion calculation engine"""
    logger.info("Initializing USPED erosion model...")
    try:
        from backend.services.erosion_model import USPEDErosionModel
        logger.info("USPED model loaded and ready for calculations")
        return True
    except Exception as e:
        logger.warning(f"Erosion model initialization: {e}")
        return False

def start_gui():
    """Start the tkinter GIS application"""
    logger.info("Launching GIS interface with map canvas...")
    try:
        from frontend.main_window import MainWindow
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        logger.error(f"Failed to start GUI app: {e}")
        return False
    return True

def display_startup_banner():
    """Display application startup information"""
    print("=" * 75)
    print("TerraSim v1.0 - Python-Only Erosion Modeling Application")
    print("=" * 75)
    print()
    print("[MODEL] PRIMARY EQUATION (USPED-Based Terrain Evolution):")
    print("─" * 75)
    print("  z(t+Δt) = z(t) - (Δt/ρ_b) * [∂(T cos α)/∂x + ∂(T sin α)/∂y")
    print("                                  + ε ∂(T sin β)/∂z]")
    print()
    print("[TRANSPORT] Sediment Flux Capacity:")
    print("  T = f(R, K, C, P, A^m, (sin β)^n, Q(I,S))")
    print()
    print("[PARAMETERS]")
    print("  R = Rainfall erosivity (MJ·mm/ha/h/yr)")
    print("  K = Soil erodibility factor (0-1)")
    print("  C = Vegetation cover factor (0-1)")
    print("  P = Management practice factor (0-1)")
    print("  A = Upslope contributing area (m²)")
    print("  β = Local slope angle")
    print("─" * 75)
    print()
    print("[CITATION] Mitasova & Hofierka (1993) USPED Model")
    print("           Mathematical Geology, Vol. 25, No. 6, pp. 657-669")
    print()
    print("[COMPONENTS STARTING]")
    print("  • Backend API (FastAPI) - REST endpoints & calculations")
    print("  • GIS Interface (Tkinter) - Interactive map & layer management")
    print("  • Erosion Engine (NumPy/SciPy) - USPED model computations")
    print("  • Database Layer (SQLAlchemy) - Results storage & retrieval")
    print()

if __name__ == "__main__":
    display_startup_banner()
    
    # Step 1: Check dependencies
    logger.info("Step 1/5: Verifying dependencies...")
    if not check_dependencies():
        logger.error("Dependency check failed")
        sys.exit(1)
    time.sleep(0.5)
    
    # Step 2: Initialize database
    logger.info("Step 2/5: Setting up database...")
    if not initialize_database():
        logger.warning("Database initialization had issues, continuing...")
    time.sleep(0.5)
    
    # Step 3: Start backend
    logger.info("Step 3/5: Starting backend...")
    if not start_backend():
        logger.warning("Backend may not be running. Continuing with local calculations...")
    time.sleep(1)
    
    # Step 4: Initialize calculation engine
    logger.info("Step 4/5: Initializing calculation engine...")
    start_calculation_engine()
    time.sleep(0.5)
    
    # Step 5: Start GUI
    logger.info("Step 5/5: Launching GIS interface...")
    print()
    time.sleep(1)
    start_gui()
