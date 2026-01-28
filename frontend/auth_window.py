"""
TerraSim Authentication Window
Login, Registration, and User Validation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
from pathlib import Path
import logging
import re
from typing import Optional, Callable
from dataclasses import dataclass
import json
from datetime import datetime, timedelta

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logger = logging.getLogger(__name__)


# ============================================================================
# USER VALIDATION
# ============================================================================

@dataclass
class UserCredentials:
    """User login credentials"""
    email: str
    password: str
    username: Optional[str] = None


class UserValidator:
    """Validate user input"""
    
    MIN_PASSWORD_LENGTH = 8
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    USERNAME_PATTERN = r'^[a-zA-Z0-9_-]{3,20}$'
    
    @staticmethod
    def validate_email(email: str) -> tuple[bool, str]:
        """Validate email format"""
        if not email or not email.strip():
            return False, "Email is required"
        
        if not re.match(UserValidator.EMAIL_PATTERN, email.strip()):
            return False, "Invalid email format"
        
        return True, ""
    
    @staticmethod
    def validate_password(password: str) -> tuple[bool, str]:
        """Validate password strength"""
        if not password:
            return False, "Password is required"
        
        if len(password) < UserValidator.MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {UserValidator.MIN_PASSWORD_LENGTH} characters"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numbers"
        
        return True, ""
    
    @staticmethod
    def validate_username(username: str) -> tuple[bool, str]:
        """Validate username format"""
        if not username or not username.strip():
            return False, "Username is required"
        
        if not re.match(UserValidator.USERNAME_PATTERN, username.strip()):
            return False, "Username must be 3-20 characters (letters, numbers, dash, underscore)"
        
        return True, ""


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Manage user sessions"""
    
    SESSION_FILE = Path(__file__).parent.parent / ".session"
    SESSION_DURATION = timedelta(days=7)
    
    def __init__(self):
        self.current_user: Optional[dict] = None
        self.token: Optional[str] = None
        self.load_session()
    
    def save_session(self, user: dict, token: str) -> None:
        """Save session to file"""
        try:
            session_data = {
                'user': user,
                'token': token,
                'timestamp': datetime.now().isoformat()
            }
            self.SESSION_FILE.write_text(json.dumps(session_data))
            self.current_user = user
            self.token = token
            logger.info(f"Session saved for user: {user.get('email')}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")
    
    def load_session(self) -> bool:
        """Load session from file"""
        try:
            if not self.SESSION_FILE.exists():
                return False
            
            data = json.loads(self.SESSION_FILE.read_text())
            
            # Check if session is still valid
            saved_time = datetime.fromisoformat(data['timestamp'])
            if datetime.now() - saved_time > self.SESSION_DURATION:
                self.clear_session()
                return False
            
            self.current_user = data['user']
            self.token = data['token']
            logger.info(f"Session loaded for user: {self.current_user.get('email')}")
            return True
        except Exception as e:
            logger.warning(f"Failed to load session: {e}")
            return False
    
    def clear_session(self) -> None:
        """Clear session"""
        try:
            if self.SESSION_FILE.exists():
                self.SESSION_FILE.unlink()
            self.current_user = None
            self.token = None
            logger.info("Session cleared")
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None and self.token is not None


# ============================================================================
# AUTHENTICATION SERVICE
# ============================================================================

class AuthenticationService:
    """Handle user authentication (login, signup, validation)"""
    
    def __init__(self):
        self.session = SessionManager()
        self.validator = UserValidator()
        self.users = self._load_users()
    
    def _load_users(self) -> dict:
        """Load users from database (simulated)"""
        try:
            from backend.db.session import SessionLocal
            from backend.models.user import User
            
            db = SessionLocal()
            users = db.query(User).all()
            db.close()
            
            return {user.email: {
                'id': user.id,
                'email': user.email,
                'hashed_password': user.hashed_password,
                'is_active': user.is_active
            } for user in users}
        except Exception as e:
            logger.warning(f"Could not load users from database: {e}")
            return {}
    
    def register(self, credentials: UserCredentials) -> tuple[bool, str]:
        """Register a new user"""
        # Validate input
        valid_email, email_msg = self.validator.validate_email(credentials.email)
        if not valid_email:
            return False, email_msg
        
        valid_pass, pass_msg = self.validator.validate_password(credentials.password)
        if not valid_pass:
            return False, pass_msg
        
        if credentials.username:
            valid_user, user_msg = self.validator.validate_username(credentials.username)
            if not valid_user:
                return False, user_msg
        
        # Check if user already exists
        if credentials.email in self.users:
            return False, "Email already registered"
        
        try:
            from backend.db.session import SessionLocal
            from backend.models.user import User
            from backend.core.security import get_password_hash, create_access_token
            
            db = SessionLocal()
            
            # Create new user
            new_user = User(
                email=credentials.email,
                hashed_password=get_password_hash(credentials.password),
                full_name=credentials.username or credentials.email.split('@')[0],
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            
            # Create token
            token = create_access_token(subject=new_user.id)
            
            # Save session
            user_data = {
                'id': new_user.id,
                'email': new_user.email,
                'full_name': new_user.full_name,
                'is_active': new_user.is_active
            }
            self.session.save_session(user_data, token)
            
            db.close()
            
            logger.info(f"User registered: {credentials.email}")
            return True, f"Welcome {credentials.email}!"
            
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return False, f"Registration error: {str(e)}"
    
    def login(self, credentials: UserCredentials) -> tuple[bool, str]:
        """Authenticate user"""
        # Validate input
        valid_email, email_msg = self.validator.validate_email(credentials.email)
        if not valid_email:
            return False, email_msg
        
        try:
            from backend.db.session import SessionLocal
            from backend.models.user import User
            from backend.core.security import verify_password, create_access_token
            
            db = SessionLocal()
            
            # Find user
            user = db.query(User).filter(User.email == credentials.email).first()
            
            if not user:
                db.close()
                return False, "Invalid email or password"
            
            if not user.is_active:
                db.close()
                return False, "Account is inactive"
            
            # Verify password
            if not verify_password(credentials.password, user.hashed_password):
                db.close()
                return False, "Invalid email or password"
            
            # Create token
            token = create_access_token(subject=user.id)
            
            # Save session
            user_data = {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active
            }
            self.session.save_session(user_data, token)
            
            db.close()
            
            logger.info(f"User logged in: {credentials.email}")
            return True, f"Welcome back, {user.full_name or user.email}!"
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False, f"Login error: {str(e)}"
    
    def logout(self) -> None:
        """Logout current user"""
        self.session.clear_session()
        logger.info("User logged out")


# ============================================================================
# LOGIN/SIGNUP WINDOW
# ============================================================================

class AuthWindow(tk.Tk):
    """Authentication window (login/signup)"""
    
    def __init__(self, on_success: Optional[Callable] = None):
        super().__init__()
        
        self.title("TerraSim - Authentication")
        self.geometry("450x550")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Set dark theme
        self.configure(bg='#0f1419')
        
        self.auth_service = AuthenticationService()
        self.on_success = on_success
        self.is_login_mode = True
        self.user: Optional[dict] = None  # Store authenticated user
        
        # Check for existing session
        if self.auth_service.session.is_authenticated():
            self._show_welcome_screen()
        else:
            self._build_login_ui()
    
    def _build_login_ui(self):
        """Build login interface"""
        # Main frame
        main_frame = tk.Frame(self, bg='#0f1419')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Label(
            main_frame,
            text="TerraSim",
            font=("Arial", 24, "bold"),
            fg="#00d9ff",
            bg='#0f1419'
        )
        header.pack(pady=(0, 10))
        
        subtitle = tk.Label(
            main_frame,
            text="Advanced Erosion Modeling Platform",
            font=("Arial", 10),
            fg="#888888",
            bg='#0f1419'
        )
        subtitle.pack(pady=(0, 20))
        
        # Mode indicator
        self.mode_label = tk.Label(
            main_frame,
            text="LOGIN",
            font=("Arial", 12, "bold"),
            fg="#00d9ff",
            bg='#0f1419'
        )
        self.mode_label.pack(pady=(0, 15))
        
        # Form frame
        form_frame = tk.Frame(main_frame, bg='#1a1f2e', relief=tk.RAISED, bd=1)
        form_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Email
        tk.Label(
            form_frame,
            text="Email",
            font=("Arial", 10),
            fg="#cccccc",
            bg='#1a1f2e'
        ).pack(anchor=tk.W, padx=15, pady=(15, 5))
        
        self.email_entry = tk.Entry(
            form_frame,
            font=("Arial", 10),
            bg='#2a2f3e',
            fg='#ffffff',
            insertbackground='#00d9ff',
            relief=tk.FLAT,
            bd=1
        )
        self.email_entry.pack(fill=tk.X, padx=15, pady=(0, 10))
        
        # Username (signup only)
        self.username_label = tk.Label(
            form_frame,
            text="Username (optional)",
            font=("Arial", 10),
            fg="#cccccc",
            bg='#1a1f2e'
        )
        
        self.username_entry = tk.Entry(
            form_frame,
            font=("Arial", 10),
            bg='#2a2f3e',
            fg='#ffffff',
            insertbackground='#00d9ff',
            relief=tk.FLAT,
            bd=1
        )
        
        # Password
        tk.Label(
            form_frame,
            text="Password",
            font=("Arial", 10),
            fg="#cccccc",
            bg='#1a1f2e'
        ).pack(anchor=tk.W, padx=15, pady=(0, 5))
        
        self.password_entry = tk.Entry(
            form_frame,
            font=("Arial", 10),
            bg='#2a2f3e',
            fg='#ffffff',
            insertbackground='#00d9ff',
            relief=tk.FLAT,
            bd=1,
            show='•'
        )
        self.password_entry.pack(fill=tk.X, padx=15, pady=(0, 15))
        
        # Password requirements (signup only)
        self.requirements_frame = tk.Frame(form_frame, bg='#1a1f2e')
        req_text = tk.Label(
            self.requirements_frame,
            text="Password must contain: uppercase, lowercase, numbers (min 8 chars)",
            font=("Arial", 8),
            fg="#888888",
            bg='#1a1f2e',
            wraplength=250,
            justify=tk.LEFT
        )
        req_text.pack()
        
        # Bind events for real-time validation
        self.password_entry.bind('<KeyRelease>', self._on_password_changed)
        
        # Error message
        self.error_label = tk.Label(
            main_frame,
            text="",
            font=("Arial", 9),
            fg="#ff6b6b",
            bg='#0f1419',
            wraplength=400,
            justify=tk.CENTER
        )
        self.error_label.pack(pady=10)
        
        # Buttons frame
        button_frame = tk.Frame(main_frame, bg='#0f1419')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Submit button
        self.submit_btn = tk.Button(
            button_frame,
            text="LOGIN",
            font=("Arial", 11, "bold"),
            bg='#00d9ff',
            fg='#000000',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._handle_login
        )
        self.submit_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Toggle button
        toggle_btn = tk.Button(
            button_frame,
            text="SIGN UP",
            font=("Arial", 11, "bold"),
            bg='#1a1f2e',
            fg='#00d9ff',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._toggle_mode
        )
        toggle_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # Forgot password
        forgot_btn = tk.Button(
            main_frame,
            text="Forgot Password?",
            font=("Arial", 9),
            bg='#0f1419',
            fg='#00d9ff',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._show_reset_password
        )
        forgot_btn.pack(pady=10)
        
        # Focus on email
        self.email_entry.focus()
    
    def _toggle_mode(self):
        """Toggle between login and signup"""
        self.is_login_mode = not self.is_login_mode
        
        if self.is_login_mode:
            self.mode_label.config(text="LOGIN")
            self.submit_btn.config(text="LOGIN")
            self.username_label.pack_forget()
            self.username_entry.pack_forget()
            self.requirements_frame.pack_forget()
        else:
            self.mode_label.config(text="SIGN UP")
            self.submit_btn.config(text="SIGN UP")
            self.username_label.pack(anchor=tk.W, padx=15, pady=(0, 5))
            self.username_entry.pack(fill=tk.X, padx=15, pady=(0, 10))
            self.requirements_frame.pack(pady=10)
        
        self._clear_form()
    
    def _clear_form(self):
        """Clear form fields"""
        self.email_entry.delete(0, tk.END)
        self.password_entry.delete(0, tk.END)
        if hasattr(self, 'username_entry'):
            self.username_entry.delete(0, tk.END)
        self.error_label.config(text="")
    
    def _on_password_changed(self, event=None):
        """Real-time password validation"""
        if not self.is_login_mode:
            password = self.password_entry.get()
            valid, msg = self.auth_service.validator.validate_password(password)
            
            if password:
                color = "#4ade80" if valid else "#ff6b6b"
                self.error_label.config(text=msg if msg else "✓ Password is strong", fg=color)
    
    def _handle_login(self):
        """Handle login/signup"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        username = self.username_entry.get().strip() if not self.is_login_mode else None
        
        credentials = UserCredentials(email=email, password=password, username=username)
        
        if self.is_login_mode:
            success, msg = self.auth_service.login(credentials)
        else:
            success, msg = self.auth_service.register(credentials)
        
        if success:
            self.error_label.config(text=msg, fg="#4ade80")
            self.after(1500, self._on_auth_success)
        else:
            self.error_label.config(text=msg, fg="#ff6b6b")
    
    def _show_reset_password(self):
        """Show password reset dialog"""
        messagebox.showinfo(
            "Password Reset",
            "Password reset feature coming soon.\n\nPlease contact support@terrasim.org"
        )
    
    def _on_auth_success(self):
        """Handle successful authentication"""
        if self.on_success:
            self.on_success(self.auth_service.session.current_user)
        self.destroy()
    
    def _show_welcome_screen(self):
        """Show welcome screen for existing session"""
        user = self.auth_service.session.current_user
        
        main_frame = tk.Frame(self, bg='#0f1419')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        header = tk.Label(
            main_frame,
            text="Welcome Back!",
            font=("Arial", 20, "bold"),
            fg="#00d9ff",
            bg='#0f1419'
        )
        header.pack(pady=(20, 10))
        
        # User info
        user_label = tk.Label(
            main_frame,
            text=f"{user['full_name']}\n{user['email']}",
            font=("Arial", 11),
            fg="#cccccc",
            bg='#0f1419'
        )
        user_label.pack(pady=20)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#0f1419')
        button_frame.pack(fill=tk.X, pady=20)
        
        tk.Button(
            button_frame,
            text="Continue",
            font=("Arial", 11, "bold"),
            bg='#00d9ff',
            fg='#000000',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._on_auth_success
        ).pack(fill=tk.X, pady=5)
        
        tk.Button(
            button_frame,
            text="Logout",
            font=("Arial", 11, "bold"),
            bg='#1a1f2e',
            fg='#ff6b6b',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._handle_logout
        ).pack(fill=tk.X, pady=5)
    
    def _handle_logout(self):
        """Handle logout"""
        self.auth_service.logout()
        self.destroy()


# ============================================================================
# MAIN
# ============================================================================

def show_auth_window(on_success: Optional[Callable] = None) -> Optional[dict]:
    """Show authentication window and return user info on success"""
    def callback(user):
        window.user = user
    
    window = AuthWindow(on_success=callback)
    window.mainloop()
    
    return getattr(window, 'user', None)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    def on_auth_success(user):
        print(f"Authenticated as: {user}")
    
    user = show_auth_window(on_success=on_auth_success)
    print(f"Final result: {user}")
