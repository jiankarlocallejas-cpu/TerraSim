"""
Device Manager Service
Tracks device logins, manages trusted devices, and logs authentication events
"""

import socket
import uuid
import platform
from typing import Optional, List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class DeviceInfo:
    """Gather current device information"""
    
    @staticmethod
    def get_device_id() -> str:
        """Get or create a unique device ID"""
        try:
            import uuid
            mac = uuid.getnode()
            return f"{mac:x}"
        except:
            return str(uuid.uuid4())
    
    @staticmethod
    def get_device_name() -> str:
        """Get device name"""
        try:
            return socket.gethostname()
        except:
            return "Unknown Device"
    
    @staticmethod
    def get_os() -> str:
        """Get operating system"""
        return platform.system()
    
    @staticmethod
    def get_os_version() -> str:
        """Get OS version"""
        return platform.release()
    
    @staticmethod
    def get_ip_address() -> str:
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"
    
    @staticmethod
    def get_browser() -> str:
        """Get browser info (if running in web context)"""
        return "Desktop App"
    
    @staticmethod
    def create_device_info() -> Dict:
        """Create device info dictionary"""
        return {
            'device_id': DeviceInfo.get_device_id(),
            'device_name': DeviceInfo.get_device_name(),
            'os': DeviceInfo.get_os(),
            'os_version': DeviceInfo.get_os_version(),
            'ip_address': DeviceInfo.get_ip_address(),
            'browser': DeviceInfo.get_browser(),
            'python_version': platform.python_version(),
        }


class DeviceManager:
    """Manage device authentication and tracking"""
    
    def __init__(self, db_session=None):
        self.session = db_session
        self.device_info = DeviceInfo.create_device_info()
    
    def register_device(self, user_id: int, device_name: str = None, is_trusted: bool = False) -> Optional[Dict]:
        """
        Register a new device for user
        Returns device info dictionary
        """
        if not self.session:
            logger.warning("No database session available for device registration")
            return None
        
        try:
            from backend.models.device import Device
            
            device_name = device_name or f"{self.device_info['os']} - {self.device_info['browser']}"
            
            device = Device(
                user_id=user_id,
                device_id=self.device_info['device_id'],
                device_name=device_name,
                os=self.device_info['os'],
                browser=self.device_info['browser'],
                ip_address=self.device_info['ip_address'],
                is_trusted=is_trusted,
                last_login=datetime.utcnow(),
                metadata=self.device_info
            )
            
            self.session.add(device)
            self.session.commit()
            
            logger.info(f"Device registered for user {user_id}: {device_name}")
            
            return {
                'id': device.id,
                'device_id': device.device_id,
                'device_name': device.device_name,
                'is_trusted': device.is_trusted,
            }
        
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            self.session.rollback()
            return None
    
    def log_login_event(self, user_id: int, device_id: int, event_type: str = "login",
                       success: bool = True, reason: str = None) -> bool:
        """Log login/signup event to database"""
        if not self.session:
            return False
        
        try:
            from backend.models.device import LoginEvent
            
            event = LoginEvent(
                user_id=user_id,
                device_id=device_id,
                event_type=event_type,
                ip_address=self.device_info['ip_address'],
                success=success,
                reason=reason,
                metadata=self.device_info
            )
            
            self.session.add(event)
            self.session.commit()
            
            logger.info(f"Login event logged: user={user_id}, event={event_type}, success={success}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to log login event: {e}")
            self.session.rollback()
            return False
    
    def get_user_devices(self, user_id: int) -> List[Dict]:
        """Get all devices for a user"""
        if not self.session:
            return []
        
        try:
            from backend.models.device import Device
            
            devices = self.session.query(Device).filter(Device.user_id == user_id).all()
            
            return [
                {
                    'id': d.id,
                    'device_id': d.device_id,
                    'device_name': d.device_name,
                    'os': d.os,
                    'browser': d.browser,
                    'ip_address': d.ip_address,
                    'is_trusted': d.is_trusted,
                    'last_login': d.last_login.isoformat() if d.last_login else None,
                    'created_at': d.created_at.isoformat() if d.created_at else None,
                }
                for d in devices
            ]
        except Exception as e:
            logger.error(f"Failed to get user devices: {e}")
            return []
    
    def get_login_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """Get login history for a user"""
        if not self.session:
            return []
        
        try:
            from backend.models.device import LoginEvent
            
            events = self.session.query(LoginEvent).filter(
                LoginEvent.user_id == user_id
            ).order_by(LoginEvent.created_at.desc()).limit(limit).all()
            
            return [
                {
                    'id': e.id,
                    'event_type': e.event_type,
                    'device_name': e.device.device_name if e.device else 'Unknown',
                    'ip_address': e.ip_address,
                    'success': e.success,
                    'reason': e.reason,
                    'created_at': e.created_at.isoformat() if e.created_at else None,
                }
                for e in events
            ]
        except Exception as e:
            logger.error(f"Failed to get login history: {e}")
            return []
    
    def trust_device(self, user_id: int, device_id: int) -> bool:
        """Mark a device as trusted"""
        if not self.session:
            return False
        
        try:
            from backend.models.device import Device
            
            device = self.session.query(Device).filter(
                Device.id == device_id,
                Device.user_id == user_id
            ).first()
            
            if device:
                device.is_trusted = True
                self.session.commit()
                logger.info(f"Device {device_id} marked as trusted for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to trust device: {e}")
            self.session.rollback()
            return False
    
    def revoke_device(self, user_id: int, device_id: int) -> bool:
        """Revoke access for a device"""
        if not self.session:
            return False
        
        try:
            from backend.models.device import Device
            
            device = self.session.query(Device).filter(
                Device.id == device_id,
                Device.user_id == user_id
            ).first()
            
            if device:
                self.session.delete(device)
                self.session.commit()
                logger.info(f"Device {device_id} revoked for user {user_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to revoke device: {e}")
            self.session.rollback()
            return False
    
    def is_device_registered(self, user_id: int) -> bool:
        """Check if current device is registered for user"""
        if not self.session:
            return False
        
        try:
            from backend.models.device import Device
            
            device = self.session.query(Device).filter(
                Device.user_id == user_id,
                Device.device_id == self.device_info['device_id']
            ).first()
            
            return device is not None
        except Exception as e:
            logger.error(f"Failed to check device: {e}")
            return False
