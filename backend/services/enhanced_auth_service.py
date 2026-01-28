"""
Enhanced Authentication Service with Email Verification and Device Tracking
"""

import logging
from typing import Optional, Tuple, Dict
from datetime import datetime, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.email_service import get_email_service
from services.device_manager import DeviceManager, DeviceInfo
from core.security import get_password_hash, verify_password, create_access_token

logger = logging.getLogger(__name__)


class EnhancedAuthService:
    """Complete authentication with email verification and device tracking"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.email_service = get_email_service()
        self.device_manager = DeviceManager(db_session)
    
    def register_user_with_verification(self, email: str, password: str, username: str, full_name: str = ""
                                       ) -> Tuple[bool, str, Optional[str]]:
        """
        Register new user and send verification email
        Returns: (success, message, verification_token)
        """
        if not self.db_session:
            return False, "Database not available", None
        
        try:
            from models.user import User
            from models.device import EmailVerification
            
            # Check if user exists
            existing = self.db_session.query(User).filter(User.email == email).first()
            if existing:
                return False, "Email already registered", None
            
            # Send verification email
            success, result = self.email_service.send_verification_email(email)
            if not success:
                return False, result, None
            
            # Store verification record
            expiry = datetime.utcnow() + timedelta(hours=24)
            verification = EmailVerification(
                email=email,
                code=result,
                is_verified=False,
                expires_at=expiry,
                metadata={
                    'username': username,
                    'full_name': full_name,
                    'password_hash': get_password_hash(password),
                    'registered_at': datetime.utcnow().isoformat()
                }
            )
            
            self.db_session.add(verification)
            self.db_session.commit()
            
            logger.info(f"Registration initiated for {email}")
            return True, f"Verification code sent to {email}. Valid for 24 hours.", result
        
        except Exception as e:
            logger.error(f"Registration error: {e}")
            self.db_session.rollback()
            return False, f"Registration failed: {str(e)}", None
    
    def verify_email(self, email: str, code: str) -> Tuple[bool, str]:
        """
        Verify email with code and complete registration
        Returns: (success, message)
        """
        if not self.db_session:
            return False, "Database not available"
        
        try:
            from models.user import User
            from models.device import EmailVerification
            
            # Verify code
            local_success, local_msg = self.email_service.verify_code(email, code)
            if not local_success:
                return False, local_msg
            
            # Get verification record
            verification = self.db_session.query(EmailVerification).filter(
                EmailVerification.email == email
            ).first()
            
            if not verification:
                return False, "Verification record not found"
            
            if verification.expires_at < datetime.utcnow():
                return False, "Verification expired"
            
            if verification.is_verified:
                return False, "Email already verified"
            
            # Create user
            metadata = verification.metadata or {}
            user = User(
                email=email,
                hashed_password=metadata.get('password_hash', ''),
                full_name=metadata.get('full_name', ''),
                is_active=True
            )
            
            self.db_session.add(user)
            self.db_session.flush()
            
            # Mark verification complete
            verification.is_verified = True
            verification.verified_at = datetime.utcnow()
            
            # Register device for user
            device_info = self.device_manager.register_device(
                user_id=user.id,
                is_trusted=False
            )
            
            # Log signup event
            if device_info:
                self.device_manager.log_login_event(
                    user_id=user.id,
                    device_id=device_info['id'],
                    event_type='signup',
                    success=True
                )
            
            self.db_session.commit()
            
            logger.info(f"User registered: {email}")
            return True, "Email verified! Registration complete. You can now login."
        
        except Exception as e:
            logger.error(f"Email verification error: {e}")
            self.db_session.rollback()
            return False, f"Verification failed: {str(e)}"
    
    def login_with_device(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        Login user and track device
        Returns: (success, message, user_info)
        """
        if not self.db_session:
            return False, "Database not available", None
        
        try:
            from models.user import User
            from models.device import Device
            
            # Find user
            user = self.db_session.query(User).filter(User.email == email).first()
            if not user:
                self.device_manager.log_login_event(
                    user_id=0,
                    device_id=0,
                    event_type='failed_login',
                    success=False,
                    reason='user_not_found'
                )
                return False, "Invalid email or password", None
            
            # Check password
            if not verify_password(password, user.hashed_password):
                device = self.db_session.query(Device).filter(
                    Device.user_id == user.id,
                    Device.device_id == DeviceInfo.get_device_id()
                ).first()
                
                self.device_manager.log_login_event(
                    user_id=user.id,
                    device_id=device.id if device else 0,
                    event_type='failed_login',
                    success=False,
                    reason='invalid_password'
                )
                return False, "Invalid email or password", None
            
            # Check if device registered
            device = self.db_session.query(Device).filter(
                Device.user_id == user.id,
                Device.device_id == DeviceInfo.get_device_id()
            ).first()
            
            if not device:
                # New device - register it
                device_info = self.device_manager.register_device(user.id)
                device_id = device_info['id'] if device_info else 0
            else:
                device_id = device.id
                device.last_login = datetime.utcnow()
                self.db_session.flush()
            
            # Log successful login
            self.device_manager.log_login_event(
                user_id=user.id,
                device_id=device_id,
                event_type='login',
                success=True
            )
            
            # Update user last login
            user.last_login = datetime.utcnow()
            self.db_session.commit()
            
            # Create token
            token = create_access_token(subject=str(user.id))
            
            logger.info(f"User logged in: {email}")
            
            return True, "Login successful", {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'token': token,
                'device_id': device_id,
            }
        
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.db_session.rollback()
            return False, f"Login failed: {str(e)}", None
    
    def require_device_verification(self, user_id: int, device_id: str = None) -> Tuple[bool, str]:
        """
        Check if device needs verification (new device login)
        Returns: (needs_verification, message)
        """
        if not self.db_session:
            return False, "Database not available"
        
        try:
            from models.device import Device
            
            device_id = device_id or DeviceInfo.get_device_id()
            
            device = self.db_session.query(Device).filter(
                Device.user_id == user_id,
                Device.device_id == device_id
            ).first()
            
            if not device:
                return True, "New device detected. Verification required."
            
            if not device.is_trusted:
                return True, "Device not trusted. Verification required."
            
            return False, "Device verified"
        
        except Exception as e:
            logger.error(f"Device verification check error: {e}")
            return False, "Error checking device"
