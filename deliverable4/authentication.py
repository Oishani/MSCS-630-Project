#!/usr/bin/env python3
"""
Authentication Module for Deliverable 4

This module implements user authentication with:
- User accounts with username/password
- Different permission levels (admin, standard)
- Session management
- Password hashing for security
"""

import hashlib
import os
import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, List, Callable
from datetime import datetime


class UserRole(Enum):
    """User permission levels."""
    ADMIN = "admin"
    STANDARD = "standard"
    GUEST = "guest"


@dataclass
class User:
    """Represents a user account."""
    username: str
    password_hash: str
    role: UserRole
    created_at: float = field(default_factory=time.time)
    last_login: Optional[float] = None
    home_directory: str = ""
    
    def __post_init__(self):
        if not self.home_directory:
            self.home_directory = f"/home/{self.username}"
    
    def check_password(self, password: str) -> bool:
        """Check if the provided password matches."""
        return self.password_hash == self._hash_password(password)
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role == UserRole.ADMIN
    
    def __str__(self) -> str:
        return f"User({self.username}, role={self.role.value})"


@dataclass
class Session:
    """Represents an active user session."""
    session_id: str
    user: User
    login_time: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def update_activity(self):
        """Update the last activity timestamp."""
        self.last_activity = time.time()
    
    def get_duration(self) -> float:
        """Get session duration in seconds."""
        return time.time() - self.login_time


@dataclass
class AuthEvent:
    """Represents an authentication event."""
    timestamp: float
    event_type: str
    username: str
    success: bool
    details: str = ""
    
    def __str__(self) -> str:
        status = "SUCCESS" if self.success else "FAILED"
        return f"[{datetime.fromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')}] {self.event_type}: {self.username} - {status} {self.details}"


class AuthenticationManager:
    """Manages user authentication and sessions."""
    
    def __init__(self, callback: Callable = None):
        """Initialize the authentication manager."""
        self.callback = callback or print
        self.users: Dict[str, User] = {}
        self.current_session: Optional[Session] = None
        self.auth_events: List[AuthEvent] = []
        self._create_default_users()
    
    def _create_default_users(self):
        """Create default system users."""
        self.register_user("admin", "admin123", UserRole.ADMIN)
        self.register_user("user1", "password1", UserRole.STANDARD)
        self.register_user("user2", "password2", UserRole.STANDARD)
        self.register_user("guest", "guest", UserRole.GUEST)
    
    def _hash_password(self, password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        return hashlib.sha256(f"{time.time()}{os.urandom(16)}".encode()).hexdigest()[:16]
    
    def _log_event(self, event_type: str, username: str, success: bool, details: str = ""):
        """Log an authentication event."""
        event = AuthEvent(timestamp=time.time(), event_type=event_type, 
                         username=username, success=success, details=details)
        self.auth_events.append(event)
        self.callback(str(event))
    
    def register_user(self, username: str, password: str, role: UserRole = UserRole.STANDARD) -> bool:
        """Register a new user."""
        if username in self.users:
            self._log_event("REGISTER", username, False, "User already exists")
            return False
        
        user = User(username=username, password_hash=self._hash_password(password), role=role)
        self.users[username] = user
        self._log_event("REGISTER", username, True, f"Role: {role.value}")
        return True
    
    def login(self, username: str, password: str) -> Optional[Session]:
        """Authenticate a user and create a session."""
        if username not in self.users:
            self._log_event("LOGIN", username, False, "User not found")
            return None
        
        user = self.users[username]
        
        if not user.check_password(password):
            self._log_event("LOGIN", username, False, "Invalid password")
            return None
        
        session = Session(session_id=self._generate_session_id(), user=user)
        user.last_login = time.time()
        self.current_session = session
        self._log_event("LOGIN", username, True, f"Session: {session.session_id}")
        return session
    
    def logout(self) -> bool:
        """Logout the current user."""
        if not self.current_session:
            return False
        
        username = self.current_session.user.username
        duration = self.current_session.get_duration()
        self._log_event("LOGOUT", username, True, f"Duration: {duration:.2f}s")
        self.current_session = None
        return True
    
    def is_authenticated(self) -> bool:
        """Check if there's an active session."""
        return self.current_session is not None
    
    def get_current_user(self) -> Optional[User]:
        """Get the current logged-in user."""
        return self.current_session.user if self.current_session else None
    
    def get_current_role(self) -> Optional[UserRole]:
        """Get the current user's role."""
        user = self.get_current_user()
        return user.role if user else None
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        if username not in self.users:
            self._log_event("CHANGE_PASSWORD", username, False, "User not found")
            return False
        
        user = self.users[username]
        if not user.check_password(old_password):
            self._log_event("CHANGE_PASSWORD", username, False, "Invalid current password")
            return False
        
        user.password_hash = self._hash_password(new_password)
        self._log_event("CHANGE_PASSWORD", username, True, "Password updated")
        return True
    
    def delete_user(self, username: str) -> bool:
        """Delete a user (admin only)."""
        if not self.is_authenticated() or not self.current_session.user.is_admin():
            self._log_event("DELETE_USER", username, False, "Admin privileges required")
            return False
        
        if username not in self.users:
            self._log_event("DELETE_USER", username, False, "User not found")
            return False
        
        if username == "admin":
            self._log_event("DELETE_USER", username, False, "Cannot delete admin")
            return False
        
        del self.users[username]
        self._log_event("DELETE_USER", username, True, f"Deleted by {self.current_session.user.username}")
        return True
    
    def list_users(self) -> List[Dict]:
        """List all users."""
        users_list = []
        is_admin = self.is_authenticated() and self.current_session.user.is_admin()
        
        for username, user in self.users.items():
            if is_admin:
                users_list.append({
                    'username': username, 'role': user.role.value,
                    'home': user.home_directory, 'last_login': user.last_login
                })
            else:
                users_list.append({'username': username, 'role': user.role.value})
        
        return users_list
    
    def get_auth_log(self, limit: int = 10) -> List[str]:
        """Get recent authentication events."""
        return [str(e) for e in self.auth_events[-limit:]]
    
    def get_session_info(self) -> Optional[Dict]:
        """Get current session information."""
        if not self.current_session:
            return None
        session = self.current_session
        return {
            'session_id': session.session_id,
            'username': session.user.username,
            'role': session.user.role.value,
            'login_time': datetime.fromtimestamp(session.login_time).strftime('%Y-%m-%d %H:%M:%S'),
            'duration': f"{session.get_duration():.2f}s"
        }


def create_auth_manager(callback: Callable = None) -> AuthenticationManager:
    """Factory function to create an authentication manager."""
    return AuthenticationManager(callback=callback)
