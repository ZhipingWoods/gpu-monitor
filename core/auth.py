"""
Simple Authentication Module
"""
import secrets
import time
from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie
from fastapi.responses import JSONResponse
import config

# In-memory session store: token -> {username, expires_at}
sessions = {}
SESSION_COOKIE_NAME = "gpu_monitor_session"


def create_session(username: str) -> str:
    """Create a new session and return the token"""
    token = secrets.token_urlsafe(32)
    sessions[token] = {
        'username': username,
        'expires_at': time.time() + config.SESSION_LIFETIME
    }
    return token


def validate_session(token: str) -> Optional[dict]:
    """Validate session token and return user data if valid"""
    if not token:
        return None

    session = sessions.get(token)
    if not session:
        return None

    if time.time() > session['expires_at']:
        # Session expired, remove it
        del sessions[token]
        return None

    return session


def logout_session(token: str):
    """Remove a session"""
    if token in sessions:
        del sessions[token]


def cleanup_sessions():
    """Remove expired sessions"""
    current_time = time.time()
    expired = [token for token, session in sessions.items()
               if current_time > session['expires_at']]
    for token in expired:
        del sessions[token]


class AuthDeps:
    """Authentication dependencies for FastAPI"""

    @staticmethod
    def get_current_user(session: str = Cookie(None)) -> str:
        """Dependency to get current authenticated user"""
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        session_data = validate_session(session)
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired session",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return session_data['username']


def require_auth(username: str = Depends(AuthDeps.get_current_user)) -> str:
    """Require authentication - returns username"""
    return username