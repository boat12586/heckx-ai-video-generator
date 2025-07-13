"""
Authentication and Authorization System for Heckx AI Video Generator
Implements JWT-based authentication, API key validation, and role-based access control
"""

import os
import jwt
import hashlib
import secrets
from datetime import datetime, timedelta
from functools import wraps
from typing import Dict, List, Optional, Union
from flask import request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash
import redis


class AuthManager:
    """Centralized authentication and authorization manager"""
    
    def __init__(self, app=None, redis_client=None):
        self.app = app
        self.redis_client = redis_client
        self.secret_key = None
        self.jwt_secret_key = None
        self.api_key = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize authentication with Flask app"""
        self.app = app
        self.secret_key = app.config.get('SECRET_KEY')
        self.jwt_secret_key = app.config.get('JWT_SECRET_KEY', self.secret_key)
        self.api_key = app.config.get('API_KEY')
        
        # Setup Redis for token blacklisting
        if not self.redis_client:
            redis_url = app.config.get('REDIS_URL', 'redis://localhost:6379')
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            except Exception as e:
                app.logger.warning(f"Redis connection failed: {e}")
                self.redis_client = None
    
    def generate_api_key(self, prefix: str = "heckx") -> str:
        """Generate a secure API key"""
        random_part = secrets.token_urlsafe(32)
        return f"{prefix}_{random_part}"
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash an API key for secure storage"""
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def verify_api_key(self, provided_key: str, stored_hash: str = None) -> bool:
        """Verify an API key against stored hash or configured key"""
        if stored_hash:
            return hashlib.sha256(provided_key.encode()).hexdigest() == stored_hash
        
        # Fallback to configured API key
        return provided_key == self.api_key
    
    def generate_jwt_token(self, payload: Dict, expires_in: int = 3600) -> str:
        """Generate JWT token with expiration"""
        payload.update({
            'exp': datetime.utcnow() + timedelta(seconds=expires_in),
            'iat': datetime.utcnow(),
            'iss': 'heckx-video-generator'
        })
        
        return jwt.encode(payload, self.jwt_secret_key, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            # Check if token is blacklisted
            if self.redis_client and self.redis_client.get(f"blacklist:{token}"):
                return None
            
            payload = jwt.decode(token, self.jwt_secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def blacklist_token(self, token: str, expires_in: int = 3600):
        """Add token to blacklist"""
        if self.redis_client:
            self.redis_client.setex(f"blacklist:{token}", expires_in, "1")
    
    def extract_token_from_request(self) -> Optional[str]:
        """Extract JWT token from request headers"""
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]
        return None
    
    def extract_api_key_from_request(self) -> Optional[str]:
        """Extract API key from request headers or query params"""
        # Check header
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return api_key
        
        # Check query parameter
        api_key = request.args.get('api_key')
        if api_key:
            return api_key
        
        return None


class RoleBasedAccessControl:
    """Role-based access control system"""
    
    ROLES = {
        'admin': {
            'permissions': ['*'],  # All permissions
            'description': 'Full system access'
        },
        'api_user': {
            'permissions': [
                'video:generate',
                'video:download',
                'project:view',
                'project:list',
                'stats:view'
            ],
            'description': 'API access for video generation'
        },
        'viewer': {
            'permissions': [
                'project:view',
                'stats:view'
            ],
            'description': 'Read-only access'
        },
        'guest': {
            'permissions': [
                'health:check'
            ],
            'description': 'Public endpoints only'
        }
    }
    
    @classmethod
    def has_permission(cls, role: str, permission: str) -> bool:
        """Check if role has specific permission"""
        if role not in cls.ROLES:
            return False
        
        role_permissions = cls.ROLES[role]['permissions']
        
        # Admin has all permissions
        if '*' in role_permissions:
            return True
        
        # Check exact permission
        if permission in role_permissions:
            return True
        
        # Check wildcard permissions
        for perm in role_permissions:
            if perm.endswith('*'):
                if permission.startswith(perm[:-1]):
                    return True
        
        return False
    
    @classmethod
    def get_role_permissions(cls, role: str) -> List[str]:
        """Get all permissions for a role"""
        return cls.ROLES.get(role, {}).get('permissions', [])


# Initialize auth manager
auth_manager = AuthManager()
rbac = RoleBasedAccessControl()


def init_auth(app, redis_client=None):
    """Initialize authentication system with app"""
    auth_manager.init_app(app)
    if redis_client:
        auth_manager.redis_client = redis_client


def require_auth(roles: Union[str, List[str]] = None, permissions: Union[str, List[str]] = None):
    """Decorator to require authentication and authorization"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip auth if disabled
            if not current_app.config.get('ENABLE_API_AUTH', False):
                g.current_user = {'role': 'admin', 'user_id': 'system'}
                return f(*args, **kwargs)
            
            # Try JWT authentication first
            token = auth_manager.extract_token_from_request()
            user_data = None
            
            if token:
                user_data = auth_manager.verify_jwt_token(token)
                if user_data:
                    g.current_user = user_data
                    auth_type = 'jwt'
                else:
                    return jsonify({'error': 'Invalid or expired token'}), 401
            
            # Fallback to API key authentication
            if not user_data:
                api_key = auth_manager.extract_api_key_from_request()
                if api_key and auth_manager.verify_api_key(api_key):
                    g.current_user = {'role': 'api_user', 'user_id': 'api_client', 'api_key': True}
                    auth_type = 'api_key'
                else:
                    return jsonify({'error': 'Authentication required'}), 401
            
            # Check role requirements
            if roles:
                required_roles = roles if isinstance(roles, list) else [roles]
                user_role = g.current_user.get('role', 'guest')
                
                if user_role not in required_roles and 'admin' not in required_roles:
                    return jsonify({'error': 'Insufficient privileges'}), 403
            
            # Check permission requirements
            if permissions:
                required_perms = permissions if isinstance(permissions, list) else [permissions]
                user_role = g.current_user.get('role', 'guest')
                
                for perm in required_perms:
                    if not rbac.has_permission(user_role, perm):
                        return jsonify({'error': f'Permission denied: {perm}'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config.get('ENABLE_API_AUTH', False):
            return f(*args, **kwargs)
        
        api_key = auth_manager.extract_api_key_from_request()
        if not api_key or not auth_manager.verify_api_key(api_key):
            return jsonify({'error': 'Valid API key required'}), 401
        
        g.current_user = {'role': 'api_user', 'user_id': 'api_client', 'api_key': True}
        return f(*args, **kwargs)
    
    return decorated_function


def public_endpoint(f):
    """Decorator to mark endpoint as public (no auth required)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        g.current_user = {'role': 'guest', 'user_id': 'anonymous'}
        return f(*args, **kwargs)
    
    return decorated_function


def get_current_user() -> Dict:
    """Get current authenticated user data"""
    return getattr(g, 'current_user', {'role': 'guest', 'user_id': 'anonymous'})


def generate_access_token(user_data: Dict, expires_in: int = 3600) -> str:
    """Generate access token for user"""
    return auth_manager.generate_jwt_token(user_data, expires_in)


def revoke_token(token: str):
    """Revoke/blacklist a JWT token"""
    auth_manager.blacklist_token(token)


# Rate limiting decorator
def rate_limit(requests_per_minute: int = 60):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_app.config.get('ENABLE_RATE_LIMITING', False):
                return f(*args, **kwargs)
            
            if not auth_manager.redis_client:
                # No Redis, skip rate limiting
                return f(*args, **kwargs)
            
            # Get client identifier
            user = get_current_user()
            client_id = user.get('user_id', request.remote_addr)
            
            # Rate limit key
            key = f"rate_limit:{client_id}:{request.endpoint}"
            
            # Check current rate
            current_requests = auth_manager.redis_client.get(key)
            if current_requests and int(current_requests) >= requests_per_minute:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'limit': requests_per_minute,
                    'window': '1 minute'
                }), 429
            
            # Increment counter
            pipe = auth_manager.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, 60)  # 1 minute window
            pipe.execute()
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class AuthMiddleware:
    """Authentication middleware for Flask app"""
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """Process request before route handler"""
        # Add request timing
        g.start_time = datetime.utcnow()
        
        # Log API requests
        if current_app.config.get('LOG_API_REQUESTS', False):
            current_app.logger.info(f"API Request: {request.method} {request.path}")
    
    def after_request(self, response):
        """Process response after route handler"""
        # Add CORS headers if enabled
        if current_app.config.get('ENABLE_CORS', False):
            origins = current_app.config.get('CORS_ORIGINS', '*')
            response.headers['Access-Control-Allow-Origin'] = origins
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-API-Key'
        
        # Add security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Add response time header
        if hasattr(g, 'start_time'):
            duration = (datetime.utcnow() - g.start_time).total_seconds()
            response.headers['X-Response-Time'] = f"{duration:.3f}s"
        
        return response


# Utility functions for setup and management
def setup_default_api_keys(app):
    """Setup default API keys for development"""
    if app.config.get('ENVIRONMENT') == 'development':
        if not app.config.get('API_KEY'):
            app.config['API_KEY'] = auth_manager.generate_api_key('dev')
            app.logger.info(f"Generated development API key: {app.config['API_KEY']}")


def create_admin_token(expires_in: int = 86400) -> str:
    """Create admin token for system operations"""
    admin_data = {
        'role': 'admin',
        'user_id': 'system_admin',
        'permissions': ['*']
    }
    return auth_manager.generate_jwt_token(admin_data, expires_in)


def validate_environment_auth_config(app) -> List[str]:
    """Validate authentication configuration"""
    warnings = []
    
    if not app.config.get('SECRET_KEY'):
        warnings.append("SECRET_KEY not set - authentication will not work")
    
    if not app.config.get('JWT_SECRET_KEY'):
        warnings.append("JWT_SECRET_KEY not set - using SECRET_KEY")
    
    if app.config.get('ENABLE_API_AUTH') and not app.config.get('API_KEY'):
        warnings.append("API authentication enabled but no API_KEY configured")
    
    if app.config.get('ENVIRONMENT') == 'production':
        if app.config.get('SECRET_KEY') == 'your-secret-key-here':
            warnings.append("Using default SECRET_KEY in production - SECURITY RISK")
    
    return warnings