from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt, set_access_cookies, set_refresh_cookies,
    unset_jwt_cookies, verify_jwt_in_request
)
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta
import re

from app import db
from app.models import User, UserRole, UserSession
from app.utils.security import validate_password_strength, generate_session_token
from app.utils.validators import validate_email, validate_employee_id

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login - returns JWT tokens in HTTP-only cookies"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Request body required'}), 400
    
    employee_id = data.get('employee_id', '').strip()
    password = data.get('password', '')
    
    if not employee_id or not password:
        return jsonify({'error': 'Employee ID and password required'}), 400
    
    # Find user
    user = User.query.filter_by(employee_id=employee_id).first()
    
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account deactivated'}), 403
    
    # Check account lockout
    if user.locked_until and user.locked_until > datetime.utcnow():
        return jsonify({
            'error': 'Account temporarily locked',
            'locked_until': user.locked_until.isoformat()
        }), 403
    
    # Verify password
    if not user.check_password(password):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= 5:
            user.locked_until = datetime.utcnow() + timedelta(minutes=15)
        db.session.commit()
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # Reset failed attempts on successful login
    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login = datetime.utcnow()
    
    # Check concurrent sessions
    active_sessions = UserSession.query.filter_by(
        user_id=user.id, is_active=True
    ).filter(UserSession.expires_at > datetime.utcnow()).count()
    
    max_sessions = current_app.config.get('MAX_CONCURRENT_SESSIONS', 3)
    if active_sessions >= max_sessions:
        # Remove oldest session
        oldest = UserSession.query.filter_by(
            user_id=user.id, is_active=True
        ).order_by(UserSession.created_at).first()
        if oldest:
            oldest.is_active = False
    
    # Create new session record
    session_token = generate_session_token()
    expires_at = datetime.utcnow() + timedelta(
        seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 3600)
    )
    session = UserSession(
        user_id=user.id,
        session_token=session_token,
        device_info=request.headers.get('User-Agent', ''),
        ip_address=request.remote_addr,
        expires_at=expires_at
    )
    db.session.add(session)
    db.session.commit()
    
    # Create tokens
    access_token = create_access_token(
        identity=user.id,
        additional_claims={
            'role': user.role.value,
            'employee_id': user.employee_id,
            'session_token': session_token
        }
    )
    refresh_token = create_refresh_token(
        identity=user.id,
        additional_claims={'session_token': session_token}
    )
    
    response = jsonify({
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    })
    
    set_access_cookies(response, access_token)
    set_refresh_cookies(response, refresh_token)
    
    return response, 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """User logout - invalidate session"""
    jwt_data = get_jwt()
    session_token = jwt_data.get('session_token')
    user_id = get_jwt_identity()
    
    if session_token:
        session = UserSession.query.filter_by(session_token=session_token).first()
        if session:
            session.is_active = False
            db.session.commit()
    
    response = jsonify({'message': 'Logged out successfully'})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    jwt_data = get_jwt()
    session_token = jwt_data.get('session_token')
    user_id = get_jwt_identity()
    
    # Verify session still valid
    session = UserSession.query.filter_by(
        session_token=session_token, is_active=True
    ).first()
    
    if not session or session.expires_at < datetime.utcnow():
        return jsonify({'error': 'Session expired'}), 401
    
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return jsonify({'error': 'User not found or inactive'}), 401
    
    access_token = create_access_token(
        identity=user_id,
        additional_claims={
            'role': user.role.value,
            'employee_id': user.employee_id,
            'session_token': session_token
        }
    )
    
    response = jsonify({'access_token': access_token})
    set_access_cookies(response, access_token)
    return response, 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    """Get current user profile"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """Change user password"""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    
    if not current_password or not new_password:
        return jsonify({'error': 'Current and new password required'}), 400
    
    if not user.check_password(current_password):
        return jsonify({'error': 'Current password incorrect'}), 400
    
    # Validate new password strength
    is_valid, message = validate_password_strength(new_password, user.employee_id, user.name)
    if not is_valid:
        return jsonify({'error': message}), 400
    
    user.set_password(new_password)
    db.session.commit()
    
    return jsonify({'message': 'Password changed successfully'}), 200


@auth_bp.route('/validate-session', methods=['GET'])
@jwt_required()
def validate_session():
    """Validate current session"""
    jwt_data = get_jwt()
    session_token = jwt_data.get('session_token')
    
    session = UserSession.query.filter_by(session_token=session_token).first()
    if not session or not session.is_active or session.expires_at < datetime.utcnow():
        return jsonify({'valid': False}), 401
    
    # Update last activity
    session.last_activity = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'valid': True}), 200


# Admin-only: Create user
@auth_bp.route('/users', methods=['POST'])
@jwt_required()
def create_user():
    """Create new user (Admin only)"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != UserRole.ADMIN.value:
        return jsonify({'error': 'Admin access required'}), 403
    
    data = request.get_json()
    
    # Validate required fields
    required = ['employee_id', 'name', 'email', 'password', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    # Validate employee_id
    if not validate_employee_id(data['employee_id']):
        return jsonify({'error': 'Invalid employee ID format'}), 400
    
    if User.query.filter_by(employee_id=data['employee_id']).first():
        return jsonify({'error': 'Employee ID already exists'}), 400
    
    # Validate email
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already exists'}), 400
    
    # Validate role
    try:
        role = UserRole(data['role'])
    except ValueError:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Validate password
    is_valid, message = validate_password_strength(data['password'], data['employee_id'], data['name'])
    if not is_valid:
        return jsonify({'error': message}), 400
    
    # Create user
    user = User(
        employee_id=data['employee_id'],
        name=data['name'],
        email=data['email'],
        role=role,
        department_id=data.get('department_id'),
        shift_pattern=data.get('shift_pattern')
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'user': user.to_dict()}), 201


# Admin-only: List users
@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    """List users (Admin only)"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != UserRole.ADMIN.value:
        return jsonify({'error': 'Admin access required'}), 403
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    role_filter = request.args.get('role')
    search = request.args.get('search', '')
    
    query = User.query
    
    if role_filter:
        try:
            query = query.filter_by(role=UserRole(role_filter))
        except ValueError:
            pass
    
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.employee_id.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


# Admin-only: Update user
@auth_bp.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """Update user (Admin only)"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != UserRole.ADMIN.value:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        if User.query.filter(User.email == data['email'], User.id != user_id).first():
            return jsonify({'error': 'Email already exists'}), 400
        user.email = data['email']
    if 'role' in data:
        try:
            user.role = UserRole(data['role'])
        except ValueError:
            return jsonify({'error': 'Invalid role'}), 400
    if 'department_id' in data:
        user.department_id = data['department_id']
    if 'shift_pattern' in data:
        user.shift_pattern = data['shift_pattern']
    if 'is_active' in data:
        user.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({'user': user.to_dict()}), 200


# Admin-only: Delete user
@auth_bp.route('/users/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """Deactivate user (Admin only)"""
    jwt_data = get_jwt()
    if jwt_data.get('role') != UserRole.ADMIN.value:
        return jsonify({'error': 'Admin access required'}), 403
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Prevent self-deletion
    current_user_id = get_jwt_identity()
    if user.id == current_user_id:
        return jsonify({'error': 'Cannot delete own account'}), 400
    
    user.is_active = False
    # Also deactivate sessions
    UserSession.query.filter_by(user_id=user_id, is_active=True).update({'is_active': False})
    
    db.session.commit()
    
    return jsonify({'message': 'User deactivated'}), 200