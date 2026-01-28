"""
Email Service for TerraSim
Handles sending verification codes and notifications
Supports multiple providers: SMTP, SendGrid, Mailgun
"""

import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Tuple
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)


class EmailConfig:
    """Email service configuration"""
    
    def __init__(self):
        self.config_file = Path(__file__).parent.parent / ".email_config"
        self.smtp_server = "smtp.gmail.com"  # Default to Gmail
        self.smtp_port = 587
        self.sender_email = ""
        self.sender_password = ""
        self.use_gmail = True
        
        self.load_config()
    
    def load_config(self):
        """Load email config from file"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.smtp_server = config.get('smtp_server', self.smtp_server)
                    self.smtp_port = config.get('smtp_port', self.smtp_port)
                    self.sender_email = config.get('sender_email', '')
                    self.sender_password = config.get('sender_password', '')
            except Exception as e:
                logger.warning(f"Failed to load email config: {e}")
    
    def save_config(self):
        """Save email config to file"""
        try:
            config = {
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port,
                'sender_email': self.sender_email,
                'sender_password': self.sender_password
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            logger.error(f"Failed to save email config: {e}")


class VerificationCode:
    """Generate and manage verification codes"""
    
    LENGTH = 6
    VALIDITY_MINUTES = 15
    
    @staticmethod
    def generate() -> str:
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(VerificationCode.LENGTH))
    
    @staticmethod
    def is_valid(created_at: datetime) -> bool:
        """Check if code is still valid"""
        expiry = created_at + timedelta(minutes=VerificationCode.VALIDITY_MINUTES)
        return datetime.now() < expiry


class EmailService:
    """Send emails and manage verification codes"""
    
    def __init__(self):
        self.config = EmailConfig()
        self.verification_codes = {}  # {email: {'code': '123456', 'created_at': datetime}}
    
    def send_verification_email(self, email: str) -> Tuple[bool, str]:
        """
        Send verification code to email
        Returns: (success, code_or_error_message)
        """
        if not self.config.sender_email or not self.config.sender_password:
            return False, "Email service not configured. See setup instructions below."
        
        # Generate verification code
        code = VerificationCode.generate()
        self.verification_codes[email] = {
            'code': code,
            'created_at': datetime.now()
        }
        
        # Create email
        subject = "TerraSim Email Verification"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>Welcome to TerraSim!</h2>
                <p>Your verification code is:</p>
                <h1 style="color: #00d9ff; font-size: 2em; letter-spacing: 0.2em;">
                    {code}
                </h1>
                <p>This code will expire in {VerificationCode.VALIDITY_MINUTES} minutes.</p>
                <p>If you didn't request this, please ignore this email.</p>
                <hr style="border: 1px solid #00d9ff;">
                <p style="color: #666; font-size: 0.9em;">
                    TerraSim - Terrain Simulation Platform
                </p>
            </body>
        </html>
        """
        
        try:
            # Send email via SMTP
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = email
            
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            logger.info(f"Verification email sent to {email}")
            return True, code
        
        except Exception as e:
            logger.error(f"Failed to send email to {email}: {e}")
            return False, f"Failed to send email: {str(e)}"
    
    def verify_code(self, email: str, code: str) -> Tuple[bool, str]:
        """
        Verify the code sent to email
        Returns: (is_valid, message)
        """
        if email not in self.verification_codes:
            return False, "No verification code sent to this email"
        
        stored = self.verification_codes[email]
        
        if not VerificationCode.is_valid(stored['created_at']):
            del self.verification_codes[email]
            return False, "Verification code expired. Request a new one."
        
        if stored['code'] != code.strip():
            return False, "Invalid verification code"
        
        # Code is valid, remove it
        del self.verification_codes[email]
        return True, "Email verified successfully"
    
    def send_device_login_alert(self, email: str, device_info: dict) -> bool:
        """Send alert for new device login"""
        if not self.config.sender_email or not self.config.sender_password:
            return False
        
        subject = "New Device Login - TerraSim"
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2>New Device Login Detected</h2>
                <p>Your account was logged in from a new device:</p>
                <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
                    <tr style="background-color: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Device</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{device_info.get('device_name', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>OS</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{device_info.get('os', 'Unknown')}</td>
                    </tr>
                    <tr style="background-color: #f0f0f0;">
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>IP Address</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{device_info.get('ip_address', 'Unknown')}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;"><strong>Time</strong></td>
                        <td style="padding: 10px; border: 1px solid #ddd;">{device_info.get('login_time', 'Unknown')}</td>
                    </tr>
                </table>
                <p>If this wasn't you, please secure your account immediately.</p>
            </body>
        </html>
        """
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.config.sender_email
            msg['To'] = email
            msg.attach(MIMEText(body, 'html'))
            
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                server.starttls()
                server.login(self.config.sender_email, self.config.sender_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            logger.error(f"Failed to send device alert: {e}")
            return False


# Global email service instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create email service instance"""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
