#!/usr/bin/env python3
"""
TerraSim - User Application
Simple, clean entry point that shows only login/signup
All backend complexity is hidden from users
"""

import sys
import os
from pathlib import Path
import logging

# Setup project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(project_root / 'terrasim.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TerraSim:
    """Main TerraSim Application Entry Point"""
    
    def __init__(self):
        self.project_root = project_root
        self.user = None
    
    def initialize_system(self) -> bool:
        """Initialize database and services on first run"""
        try:
            logger.info("Initializing TerraSim system...")
            
            # Initialize database
            from backend.db.session import init_db
            init_db()
            logger.info("✓ Database initialized")
            
            # Initialize email service
            from backend.services.email_service import EmailConfig
            config = EmailConfig()
            if config.sender_email:
                logger.info("✓ Email service configured")
            else:
                logger.warning("⚠ Email service not configured (optional)")
            
            # Initialize device manager
            logger.info("✓ Device tracking ready")
            
            return True
        
        except Exception as e:
            logger.error(f"Initialization error: {e}")
            return False
    
    def show_login_signup(self) -> bool:
        """Show authentication window to user"""
        try:
            logger.info("Launching authentication window...")
            
            from frontend.auth_window import show_auth_window
            user = show_auth_window()
            
            if user:
                self.user = user
                logger.info(f"User logged in: {user.get('email')}")
                return True
            else:
                logger.info("User cancelled login")
                return False
        
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def launch_main_application(self) -> int:
        """Launch main application after authentication"""
        try:
            logger.info(f"Launching main application for {self.user.get('email')}...")
            
            # Launch GIS interface
            from frontend.main_gis import TerraSim_GIS
            
            app = TerraSim_GIS()
            app.mainloop()
            
            return 0
        
        except Exception as e:
            logger.error(f"Application launch error: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    def run(self) -> int:
        """Main application flow"""
        logger.info("="*60)
        logger.info("TerraSim - Terrain Simulation Platform")
        logger.info("="*60)
        
        # Step 1: Initialize system
        if not self.initialize_system():
            logger.error("System initialization failed")
            return 1
        
        # Step 2: Show login/signup
        while True:
            if self.show_login_signup():
                break
            else:
                # User cancelled, ask if they want to exit
                print("\nExit TerraSim? (yes/no): ", end="")
                if input().lower().startswith('y'):
                    logger.info("TerraSim exited by user")
                    return 0
        
        # Step 3: Launch main application
        return self.launch_main_application()


def main():
    """Entry point"""
    try:
        app = TerraSim()
        return app.run()
    except KeyboardInterrupt:
        logger.info("TerraSim interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
