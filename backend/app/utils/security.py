from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt
from app.models import UserRole


def role_required(*roles):
    """Decorator to require specific roles"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            jwt_data = get_jwt()
            user_role = jwt_data.get('role')
            
            if user_role not in [r.value for r in roles]:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """Decorator to require admin role"""
    return role_required(UserRole.ADMIN)(fn)


def supervisor_required(fn):
    """Decorator to require supervisor or admin role"""
    return role_required(UserRole.SUPERVISOR, UserRole.ADMIN)(fn)


def operator_required(fn):
    """Decorator to require operator, supervisor, or admin role"""
    return role_required(UserRole.OPERATOR, UserRole.SUPERVISOR, UserRole.ADMIN)(fn)


def self_or_admin_required(user_id_param='user_id'):
    """Decorator to allow access to own resources or admin"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            jwt_data = get_jwt()
            user_role = jwt_data.get('role')
            current_user_id = jwt_data.get('sub')
            
            # Admin can access everything
            if user_role == UserRole.ADMIN.value:
                return fn(*args, **kwargs)
            
            # Check if accessing own resource
            target_user_id = kwargs.get(user_id_param)
            if target_user_id and int(target_user_id) == current_user_id:
                return fn(*args, **kwargs)
            
            return jsonify({'error': 'Access denied'}), 403
        return wrapper
    return decorator


def rate_limit(max_requests=100, window_seconds=60):
    """Simple rate limiting decorator (use Redis in production)"""
    from collections import defaultdict
    import time
    
    requests = defaultdict(list)
    
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            from flask import request
            ip = request.remote_addr
            now = time.time()
            
            # Clean old requests
            requests[ip] = [t for t in requests[ip] if now - t < window_seconds]
            
            if len(requests[ip]) >= max_requests:
                return jsonify({'error': 'Rate limit exceeded'}), 429
            
            requests[ip].append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator