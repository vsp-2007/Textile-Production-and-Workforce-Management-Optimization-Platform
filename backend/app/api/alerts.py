from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta

from app import db
from app.models import Alert, AlertType, AlertSeverity, User, UserRole
from app.utils.security import supervisor_required, admin_required

alerts_bp = Blueprint('alerts', __name__)


@alerts_bp.route('', methods=['GET'])
@jwt_required()
def list_alerts():
    """List alerts with filters"""
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    current_user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    alert_type = request.args.get('type')
    severity = request.args.get('severity')
    is_read = request.args.get('is_read')
    machine_id = request.args.get('machine_id', type=int)
    operator_id = request.args.get('operator_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    query = Alert.query
    
    # Operators only see alerts related to them
    if user_role == UserRole.OPERATOR.value:
        query = query.filter(
            or_(
                Alert.operator_id == current_user_id,
                Alert.machine_id.in_(
                    db.session.query(ShiftAssignment.machine_id).filter(
                        ShiftAssignment.operator_id == current_user_id,
                        ShiftAssignment.status == AssignmentStatus.STARTED
                    )
                )
            )
        )
    
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(Alert.created_at >= since)
    
    if alert_type:
        try:
            query = query.filter_by(alert_type=AlertType(alert_type))
        except ValueError:
            pass
    
    if severity:
        try:
            query = query.filter_by(severity=AlertSeverity(severity))
        except ValueError:
            pass
    
    if is_read is not None:
        query = query.filter_by(is_read=is_read.lower() == 'true')
    
    if machine_id:
        query = query.filter_by(machine_id=machine_id)
    
    if operator_id:
        query = query.filter_by(operator_id=operator_id)
    
    pagination = query.order_by(Alert.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'alerts': [a.to_dict() for a in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@alerts_bp.route('/unread-count', methods=['GET'])
@jwt_required()
def get_unread_count():
    """Get unread alert count for current user"""
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    current_user_id = get_jwt_identity()
    
    query = Alert.query.filter_by(is_read=False)
    
    if user_role == UserRole.OPERATOR.value:
        query = query.filter(
            or_(
                Alert.operator_id == current_user_id,
                Alert.machine_id.in_(
                    db.session.query(ShiftAssignment.machine_id).filter(
                        ShiftAssignment.operator_id == current_user_id,
                        ShiftAssignment.status == AssignmentStatus.STARTED
                    )
                )
            )
        )
    elif user_role in [UserRole.SUPERVISOR.value, UserRole.ADMIN.value]:
        # Supervisors see all unread alerts
        pass
    
    count = query.count()
    return jsonify({'unread_count': count}), 200


@alerts_bp.route('/<int:alert_id>/acknowledge', methods=['PUT'])
@jwt_required()
def acknowledge_alert(alert_id):
    """Acknowledge an alert"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    current_user_id = get_jwt_identity()
    
    # Check permissions
    if user_role == UserRole.OPERATOR.value:
        # Operators can only acknowledge alerts assigned to them or their machines
        if alert.operator_id != current_user_id:
            # Check if it's their machine
            assignment = ShiftAssignment.query.filter_by(
                operator_id=current_user_id,
                machine_id=alert.machine_id,
                status=AssignmentStatus.STARTED
            ).first()
            if not assignment:
                return jsonify({'error': 'Access denied'}), 403
    
    alert.is_read = True
    alert.acknowledged_at = datetime.utcnow()
    alert.acknowledged_by = current_user_id
    db.session.commit()
    
    # Emit real-time update
    from app import socketio
    socketio.emit('alert_acknowledged', {
        'alert_id': alert_id,
        'acknowledged_by': current_user_id,
        'acknowledged_at': alert.acknowledged_at.isoformat()
    }, room='supervisors')
    
    return jsonify({'alert': alert.to_dict()}), 200


@alerts_bp.route('/acknowledge-all', methods=['PUT'])
@supervisor_required
def acknowledge_all_alerts():
    """Acknowledge all unread alerts (Supervisor only)"""
    data = request.get_json() or {}
    alert_type = data.get('type')
    machine_id = data.get('machine_id')
    
    query = Alert.query.filter_by(is_read=False)
    
    if alert_type:
        try:
            query = query.filter_by(alert_type=AlertType(alert_type))
        except ValueError:
            pass
    
    if machine_id:
        query = query.filter_by(machine_id=machine_id)
    
    alerts = query.all()
    current_user_id = get_jwt_identity()
    
    for alert in alerts:
        alert.is_read = True
        alert.acknowledged_at = datetime.utcnow()
        alert.acknowledged_by = current_user_id
    
    db.session.commit()
    
    return jsonify({'acknowledged': len(alerts)}), 200


@alerts_bp.route('/types', methods=['GET'])
@jwt_required()
def list_alert_types():
    """List all alert types"""
    types = [{'value': t.value, 'label': t.value.replace('_', ' ').title()} for t in AlertType]
    severities = [{'value': s.value, 'label': s.value.title()} for s in AlertSeverity]
    return jsonify({'types': types, 'severities': severities}), 200