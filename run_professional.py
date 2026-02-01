#!/usr/bin/env python
"""
TerraSim Professional - Quick Start
Launches the professional erosion analysis UI
"""

import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "frontend"))


def main():
    """Run TerraSim Professional"""
    logger.info("Starting TerraSim Professional...")
    
    try:
        # Try to import standalone version first (no dependencies)
        try:
            from frontend.professional_ui_standalone import ProfessionalMainWindowStandalone
            logger.info("Launching professional interface (standalone)...")
            app = ProfessionalMainWindowStandalone()
            app.mainloop()
        except ImportError:
            # Fall back to full version if standalone not available
            logger.info("Trying full version with backend integration...")
            from frontend.professional_ui import ProfessionalMainWindow
            logger.info("Launching professional interface...")
            app = ProfessionalMainWindow()
            app.mainloop()
        
    except Exception as e:
        logger.error(f"Error starting application: {e}", exc_info=True)
        print(f"\nError: {e}")
        print("Make sure tkinter is installed: pip install tk")
        sys.exit(1)


if __name__ == "__main__":
    main()
