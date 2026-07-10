"""
WebSocket handlers for real-time updates
"""

from flask import request
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room, disconnect
from app import socketio
from app.models import User, UserRole


@socketio.on('connect')
def handle_connect(auth):
    """Handle client connection"""
    # Expect JWT token in auth
    token = auth.get('token') if auth else None
    
    if not token:
        # Try to get from query string
        token = request.args.get('token')
    
    if not token:
        return False  # Reject connection
    
    try:
        decoded = decode_token(token)
        user_id = decoded['sub']
        role = decoded.get('role')
        
        # Join role-based room
        if role in [UserRole.SUPERVISOR.value, UserRole.ADMIN.value]:
            join_room('supervisors')
        elif role == UserRole.OPERATOR.value:
            join_room(f'operator_{user_id}')
        
        # Store user info in session
        from flask import session
        session['user_id'] = user_id
        session['role'] = role
        
        emit('connected', {'user_id': user_id, 'role': role})
        return True
        
    except Exception as e:
        print(f"WebSocket auth error: {e}")
        return False


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import session
    user_id = session.get('user_id')
    role = session.get('role')
    
    if role in [UserRole.SUPERVISOR.value, UserRole.ADMIN.value]:
        leave_room('supervisors')
    elif role == UserRole.OPERATOR.value:
        leave_room(f'operator_{user_id}')


@socketio.on('join_shift')
def handle_join_shift(data):
    """Join a shift-specific room for updates"""
    shift_id = data.get('shift_id')
    if shift_id:
        join_room(f'shift_{shift_id}')
        emit('joined_shift', {'shift_id': shift_id})


@socketio.on('leave_shift')
def handle_leave_shift(data):
    """Leave a shift-specific room"""
    shift_id = data.get('shift_id')
    if shift_id:
        leave_room(f'shift_{shift_id}')
        emit('left_shift', {'shift_id': shift_id})


@socketio.on('subscribe_machine')
def handle_subscribe_machine(data):
    """Subscribe to machine-specific updates"""
    machine_id = data.get('machine_id')
    if machine_id:
        join_room(f'machine_{machine_id}')
        emit('subscribed_machine', {'machine_id': machine_id})


@socketio.on('unsubscribe_machine')
def handle_unsubscribe_machine(data):
    """Unsubscribe from machine updates"""
    machine_id = data.get('machine_id')
    if machine_id:
        leave_room(f'machine_{machine_id}')
        emit('unsubscribed_machine', {'machine_id': machine_id})


@socketio.on('ping')
def handle_ping():
    """Health check"""
    emit('pong', {'timestamp': __import__('datetime').datetime.utcnow().isoformat()})


def register_websocket_handlers(socketio_instance):
    """Register all WebSocket handlers"""
    # Handlers are registered via decorators above
    pass


# Helper functions for emitting events
def emit_machine_update(machine_id, data):
    """Emit machine update to relevant rooms"""
    socketio.emit('machine_update', data, room=f'machine_{machine_id}')
    socketio.emit('machine_update', data, room='supervisors')


def emit_shift_update(shift_id, data):
    """Emit shift update to shift room"""
    socketio.emit('shift_update', data, room=f'shift_{shift_id}')
    socketio.emit('shift_update', data, room='supervisors')


def emit_alert(alert_data):
    """Emit new alert to supervisors"""
    socketio.emit('new_alert', alert_data, room='supervisors')


def emit_assignment_change(shift_id, data):
    """Emit assignment change"""
    socketio.emit('assignment_change', data, room=f'shift_{shift_id}')
    socketio.emit('assignment_change', data, room='supervisors')