"""
TerraSim OAuth Authentication Window
Login via Google, GitHub, or Traditional Credentials
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import sys
from pathlib import Path
import logging
from typing import Optional, Callable, Dict, Any
from dataclasses import dataclass
import json
from datetime import datetime, timedelta
from threading import Thread

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

logger = logging.getLogger(__name__)


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
        self.oauth_provider: Optional[str] = None
        self.load_session()
    
    def save_session(self, user: dict, token: str, oauth_provider: Optional[str] = None) -> None:
        """Save session to file"""
        try:
            session_data = {
                'user': user,
                'token': token,
                'oauth_provider': oauth_provider,
                'timestamp': datetime.now().isoformat()
            }
            self.SESSION_FILE.write_text(json.dumps(session_data))
            self.current_user = user
            self.token = token
            self.oauth_provider = oauth_provider
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
            self.oauth_provider = data.get('oauth_provider')
            if self.current_user:
                logger.info(f"Session loaded for user: {self.current_user.get('email', 'Unknown')}")
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
            self.oauth_provider = None
            logger.info("Session cleared")
        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return self.current_user is not None and self.token is not None


# ============================================================================
# OAUTH AUTHENTICATION WINDOW
# ============================================================================

class OAuthAuthWindow(tk.Tk):
    """OAuth Authentication Window"""
    
    def __init__(self, on_success: Optional[Callable] = None):
        super().__init__()
        
        self.title("TerraSim - OAuth Authentication")
        self.geometry("500x600")
        self.resizable(False, False)
        
        # Center window
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Set dark theme
        self.configure(bg='#0f1419')
        
        self.session = SessionManager()
        self.on_success = on_success
        self.user: Optional[dict] = None
        self.oauth_provider: Optional[str] = None
        
        # Check for existing session
        if self.session.is_authenticated():
            self._show_welcome_screen()
        else:
            self._build_oauth_ui()
    
    def _build_oauth_ui(self):
        """Build OAuth authentication interface"""
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
        subtitle.pack(pady=(0, 30))
        
        # OAuth section
        oauth_label = tk.Label(
            main_frame,
            text="Sign In With",
            font=("Arial", 11, "bold"),
            fg="#cccccc",
            bg='#0f1419'
        )
        oauth_label.pack(pady=(0, 15))
        
        # OAuth buttons
        button_frame = tk.Frame(main_frame, bg='#0f1419')
        button_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Google OAuth button
        google_btn = tk.Button(
            button_frame,
            text="🔵 Google",
            font=("Arial", 11, "bold"),
            bg='#ffffff',
            fg='#000000',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._authenticate_google,
            padx=20,
            pady=12
        )
        google_btn.pack(fill=tk.X, pady=(0, 10))
        
        # GitHub OAuth button
        github_btn = tk.Button(
            button_frame,
            text="⚫ GitHub",
            font=("Arial", 11, "bold"),
            bg='#2d2d2d',
            fg='#ffffff',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._authenticate_github,
            padx=20,
            pady=12
        )
        github_btn.pack(fill=tk.X, pady=(0, 30))
        
        # Divider
        divider = tk.Label(
            main_frame,
            text="OR",
            font=("Arial", 9),
            fg="#666666",
            bg='#0f1419'
        )
        divider.pack(pady=(0, 20))
        
        # Traditional login option
        traditional_label = tk.Label(
            main_frame,
            text="Traditional Login",
            font=("Arial", 11, "bold"),
            fg="#cccccc",
            bg='#0f1419'
        )
        traditional_label.pack(pady=(0, 15))
        
        # Email
        tk.Label(
            main_frame,
            text="Email",
            font=("Arial", 10),
            fg="#cccccc",
            bg='#0f1419'
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.email_entry = tk.Entry(
            main_frame,
            font=("Arial", 10),
            bg='#2a2f3e',
            fg='#ffffff',
            insertbackground='#00d9ff',
            relief=tk.FLAT,
            bd=1,
            width=30
        )
        self.email_entry.pack(fill=tk.X, pady=(0, 15))
        
        # Password
        tk.Label(
            main_frame,
            text="Password",
            font=("Arial", 10),
            fg="#cccccc",
            bg='#0f1419'
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.password_entry = tk.Entry(
            main_frame,
            font=("Arial", 10),
            bg='#2a2f3e',
            fg='#ffffff',
            insertbackground='#00d9ff',
            relief=tk.FLAT,
            bd=1,
            width=30,
            show='•'
        )
        self.password_entry.pack(fill=tk.X, pady=(0, 15))
        
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
        
        # Traditional login button
        login_btn = tk.Button(
            main_frame,
            text="LOGIN",
            font=("Arial", 11, "bold"),
            bg='#00d9ff',
            fg='#000000',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._handle_traditional_login,
            padx=20,
            pady=12
        )
        login_btn.pack(fill=tk.X, pady=(10, 0))
        
        # Sign up link
        signup_label = tk.Label(
            main_frame,
            text="Don't have an account? Sign up",
            font=("Arial", 9),
            fg="#00d9ff",
            bg='#0f1419',
            cursor='hand2'
        )
        signup_label.pack(pady=(15, 0))
        signup_label.bind('<Button-1>', lambda e: self._show_signup())
    
    def _authenticate_google(self):
        """Authenticate with Google OAuth"""
        try:
            from backend.core.oauth_service import get_oauth_service
            
            oauth_service = get_oauth_service()
            
            if not oauth_service.is_provider_available('google'):
                messagebox.showerror(
                    "Error",
                    "Google OAuth is not configured.\n"
                    "Please set OAUTH_GOOGLE_CLIENT_ID and OAUTH_GOOGLE_CLIENT_SECRET environment variables."
                )
                return
            
            auth_url, state = oauth_service.get_authorization_url('google')
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Show callback window
            self._show_callback_window('google', state)
            
        except Exception as e:
            logger.error(f"Google OAuth error: {e}")
            messagebox.showerror("Error", f"Google authentication failed: {str(e)}")
    
    def _authenticate_github(self):
        """Authenticate with GitHub OAuth"""
        try:
            from backend.core.oauth_service import get_oauth_service
            
            oauth_service = get_oauth_service()
            
            if not oauth_service.is_provider_available('github'):
                messagebox.showerror(
                    "Error",
                    "GitHub OAuth is not configured.\n"
                    "Please set OAUTH_GITHUB_CLIENT_ID and OAUTH_GITHUB_CLIENT_SECRET environment variables."
                )
                return
            
            auth_url, state = oauth_service.get_authorization_url('github')
            
            # Open browser for authentication
            webbrowser.open(auth_url)
            
            # Show callback window
            self._show_callback_window('github', state)
            
        except Exception as e:
            logger.error(f"GitHub OAuth error: {e}")
            messagebox.showerror("Error", f"GitHub authentication failed: {str(e)}")
    
    def _show_callback_window(self, provider: str, state: str):
        """Show callback window with authorization code input"""
        callback_window = tk.Toplevel(self)
        callback_window.title(f"Authorize {provider.title()}")
        callback_window.geometry("500x300")
        callback_window.transient(self)
        callback_window.grab_set()
        
        # Instructions
        instructions = tk.Label(
            callback_window,
            text=f"After authorizing, copy the code from the browser and paste it below.",
            font=("Arial", 10),
            wraplength=450
        )
        instructions.pack(pady=20, padx=20)
        
        # Code entry
        tk.Label(callback_window, text="Authorization Code:").pack(anchor=tk.W, padx=20)
        code_entry = tk.Entry(callback_window, font=("Arial", 10), width=50)
        code_entry.pack(pady=10, padx=20)
        code_entry.focus()
        
        def submit_code():
            code = code_entry.get().strip()
            if not code:
                messagebox.showwarning("Warning", "Please enter the authorization code")
                return
            
            try:
                from backend.core.oauth_service import get_oauth_service
                from backend.core.security import create_access_token
                
                oauth_service = get_oauth_service()
                result = oauth_service.authenticate(provider, code)
                
                user_info = result['user']
                access_token = result.get('access_token', create_access_token(subject=user_info['provider_id']))
                
                # Save session
                user_data = {
                    'id': user_info.get('provider_id') if user_info else None,
                    'email': user_info.get('email') if user_info else None,
                    'name': user_info.get('name') if user_info else None,
                    'picture_url': user_info.get('picture_url') if user_info else None,
                    'provider': provider
                }
                
                self.session.save_session(user_data, access_token, provider)
                self.user = user_data
                self.oauth_provider = provider
                
                callback_window.destroy()
                self._show_welcome_screen()
                
                if self.on_success:
                    self.on_success(self.user)
                
            except Exception as e:
                logger.error(f"Authentication error: {e}")
                messagebox.showerror("Error", f"Authentication failed: {str(e)}")
        
        submit_btn = tk.Button(
            callback_window,
            text="Authorize",
            font=("Arial", 11, "bold"),
            command=submit_code,
            padx=20,
            pady=10
        )
        submit_btn.pack(pady=20)
    
    def _handle_traditional_login(self):
        """Handle traditional email/password login"""
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        
        if not email or not password:
            self.error_label.config(text="Email and password are required")
            return
        
        try:
            from backend.db.session import SessionLocal
            from backend.models.user import User
            from backend.core.security import verify_password, create_access_token
            
            db = SessionLocal()
            user = db.query(User).filter(User.email == email).first()
            
            if not user or not verify_password(password, user.hashed_password):
                self.error_label.config(text="Invalid email or password")
                db.close()
                return
            
            if not user.is_active:
                self.error_label.config(text="Account is inactive")
                db.close()
                return
            
            # Create token
            token = create_access_token(subject=user.id)
            
            # Save session
            user_data = {
                'id': user.id,
                'email': user.email,
                'name': user.full_name,
                'provider': 'traditional'
            }
            
            self.session.save_session(user_data, token, 'traditional')
            self.user = user_data
            self.oauth_provider = 'traditional'
            
            db.close()
            
            self._show_welcome_screen()
            
            if self.on_success:
                self.on_success(self.user)
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            self.error_label.config(text=f"Login failed: {str(e)}")
    
    def _show_signup(self):
        """Show signup dialog"""
        messagebox.showinfo(
            "Sign Up",
            "Sign up functionality will be available soon.\n"
            "For now, please use OAuth to sign in."
        )
    
    def _show_welcome_screen(self):
        """Show welcome screen after authentication"""
        # Clear existing widgets
        for widget in self.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self, bg='#0f1419')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Welcome message
        welcome_text = "Welcome, User!"
        if self.session.current_user:
            welcome_text = f"Welcome, {self.session.current_user.get('name', 'User')}!"
        
        welcome_label = tk.Label(
            main_frame,
            text=welcome_text,
            font=("Arial", 18, "bold"),
            fg="#00d9ff",
            bg='#0f1419'
        )
        welcome_label.pack(pady=(50, 20))
        
        # User info
        email_text = "Email: Unknown"
        if self.session.current_user:
            email_text = f"Email: {self.session.current_user.get('email', 'Unknown')}"
        
        email_label = tk.Label(
            main_frame,
            text=email_text,
            font=("Arial", 11),
            fg="#cccccc",
            bg='#0f1419'
        )
        email_label.pack(pady=5)
        
        provider_text = f"Signed in via: {self.session.oauth_provider or 'Traditional'}"
        provider_label = tk.Label(
            main_frame,
            text=provider_text,
            font=("Arial", 11),
            fg="#888888",
            bg='#0f1419'
        )
        provider_label.pack(pady=5)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#0f1419')
        button_frame.pack(pady=(50, 0))
        
        continue_btn = tk.Button(
            button_frame,
            text="Continue to TerraSim",
            font=("Arial", 12, "bold"),
            bg='#00d9ff',
            fg='#000000',
            relief=tk.FLAT,
            cursor='hand2',
            command=self.destroy,
            padx=30,
            pady=12
        )
        continue_btn.pack(side=tk.LEFT, padx=5)
        
        logout_btn = tk.Button(
            button_frame,
            text="Logout",
            font=("Arial", 12, "bold"),
            bg='#1a1f2e',
            fg='#00d9ff',
            relief=tk.FLAT,
            cursor='hand2',
            command=self._logout,
            padx=30,
            pady=12
        )
        logout_btn.pack(side=tk.LEFT, padx=5)
    
    def _logout(self):
        """Logout user"""
        self.session.clear_session()
        self.user = None
        self.oauth_provider = None
        
        # Rebuild login UI
        for widget in self.winfo_children():
            widget.destroy()
        self._build_oauth_ui()


def show_auth_window(on_success: Optional[Callable] = None) -> Optional[Dict[str, Any]]:
    """Show authentication window and return user data"""
    auth_window = OAuthAuthWindow(on_success=on_success)
    auth_window.mainloop()
    
    if auth_window.session.is_authenticated():
        return auth_window.session.current_user
    return None


if __name__ == "__main__":
    # Test the OAuth window
    user = show_auth_window()
    if user:
        print(f"Authenticated user: {user}")
    else:
        print("Authentication cancelled")
