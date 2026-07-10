from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta

from app import db
from app.models import (
    User, UserRole, Certification, OperatorCertification, CertificationStatus,
    Machine, MachineType, Shift, ShiftAssignment, AssignmentStatus,
    MachineStatus, Alert, AlertType, AlertSeverity
)
from app.utils.security import supervisor_required, admin_required, self_or_admin_required
from app.utils.validators import validate_certification_code

operators_bp = Blueprint('operators', __name__)


@operators_bp.route('', methods=['GET'])
@jwt_required()
def list_operators():
    """List all operators with filters"""
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    current_user_id = get_jwt_identity()
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    search = request.args.get('search', '')
    cert_filter = request.args.get('certification_id', type=int)
    department_filter = request.args.get('department_id', type=int)
    shift_pattern = request.args.get('shift_pattern')
    only_available = request.args.get('available', 'false').lower() == 'true'
    
    # Operators can only see themselves unless supervisor/admin
    if user_role == UserRole.OPERATOR.value:
        query = User.query.filter_by(id=current_user_id, role=UserRole.OPERATOR)
    else:
        query = User.query.filter_by(role=UserRole.OPERATOR, is_active=True)
    
    if search:
        query = query.filter(
            or_(
                User.name.ilike(f'%{search}%'),
                User.employee_id.ilike(f'%{search}%')
            )
        )
    
    if department_filter:
        query = query.filter_by(department_id=department_filter)
    
    if shift_pattern:
        query = query.filter_by(shift_pattern=shift_pattern)
    
    if cert_filter:
        query = query.join(OperatorCertification).filter(
            OperatorCertification.certification_id == cert_filter,
            OperatorCertification.status == CertificationStatus.ACTIVE
        )
    
    if only_available:
        # This would require checking current shift assignments
        # For now, return all
        pass
    
    pagination = query.order_by(User.name).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    operators = []
    for op in pagination.items:
        op_data = op.to_dict()
        # Include certifications
        certs = OperatorCertification.query.filter_by(
            user_id=op.id, status=CertificationStatus.ACTIVE
        ).all()
        op_data['certifications'] = [c.to_dict() for c in certs if c.is_valid()]
        operators.append(op_data)
    
    return jsonify({
        'operators': operators,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@operators_bp.route('/<int:operator_id>', methods=['GET'])
@jwt_required()
def get_operator(operator_id):
    """Get operator details with certifications and schedule"""
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    current_user_id = get_jwt_identity()
    
    # Operators can only view themselves
    if user_role == UserRole.OPERATOR.value and operator_id != current_user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    operator = User.query.filter_by(id=operator_id, role=UserRole.OPERATOR).first()
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    op_data = operator.to_dict()
    
    # Get certifications
    certs = OperatorCertification.query.filter_by(user_id=operator_id).all()
    op_data['certifications'] = [c.to_dict() for c in certs]
    
    # Get upcoming shifts
    upcoming_shifts = ShiftAssignment.query.filter(
        ShiftAssignment.operator_id == operator_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
    ).join(Shift).order_by(Shift.start_time).limit(10).all()
    
    op_data['upcoming_shifts'] = [s.to_dict() for s in upcoming_shifts]
    
    return jsonify({'operator': op_data}), 200


@operators_bp.route('/<int:operator_id>/schedule', methods=['GET'])
@jwt_required()
def get_operator_schedule(operator_id):
    """Get operator's shift schedule"""
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    current_user_id = get_jwt_identity()
    
    if user_role == UserRole.OPERATOR.value and operator_id != current_user_id:
        return jsonify({'error': 'Access denied'}), 403
    
    operator = User.query.filter_by(id=operator_id, role=UserRole.OPERATOR).first()
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    # Date range filter
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = ShiftAssignment.query.filter_by(operator_id=operator_id).join(Shift)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(ShiftAssignment.assigned_at >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(ShiftAssignment.assigned_at <= end_dt)
        except ValueError:
            pass
    
    assignments = query.order_by(Shift.start_time).all()
    
    return jsonify({
        'schedule': [a.to_dict() for a in assignments]
    }), 200


@operators_bp.route('/<int:operator_id>/certifications', methods=['POST'])
@admin_required
def add_certification(operator_id):
    """Add/update operator certification"""
    operator = User.query.filter_by(id=operator_id, role=UserRole.OPERATOR).first()
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    data = request.get_json()
    
    required = ['certification_id', 'obtained_date']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    cert = Certification.query.get(data['certification_id'])
    if not cert:
        return jsonify({'error': 'Certification not found'}), 404
    
    try:
        obtained_date = datetime.strptime(data['obtained_date'], '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid obtained_date format (YYYY-MM-DD)'}), 400
    
    expiry_date = None
    if data.get('expiry_date'):
        try:
            expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid expiry_date format (YYYY-MM-DD)'}), 400
    elif cert.validity_months:
        from dateutil.relativedelta import relativedelta
        expiry_date = obtained_date + relativedelta(months=cert.validity_months)
    
    # Check if already exists
    existing = OperatorCertification.query.filter_by(
        user_id=operator_id, certification_id=cert.id
    ).first()
    
    if existing:
        existing.obtained_date = obtained_date
        existing.expiry_date = expiry_date
        existing.status = CertificationStatus.ACTIVE
        existing.issued_by = get_jwt_identity()
        existing.notes = data.get('notes')
        existing.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'certification': existing.to_dict()}), 200
    
    op_cert = OperatorCertification(
        user_id=operator_id,
        certification_id=cert.id,
        obtained_date=obtained_date,
        expiry_date=expiry_date,
        status=CertificationStatus.ACTIVE,
        issued_by=get_jwt_identity(),
        notes=data.get('notes')
    )
    
    db.session.add(op_cert)
    db.session.commit()
    
    return jsonify({'certification': op_cert.to_dict()}), 201


@operators_bp.route('/<int:operator_id>/certifications/<int:cert_id>', methods=['PUT'])
@admin_required
def update_certification(operator_id, cert_id):
    """Update operator certification"""
    op_cert = OperatorCertification.query.filter_by(
        user_id=operator_id, certification_id=cert_id
    ).first()
    
    if not op_cert:
        return jsonify({'error': 'Certification not found'}), 404
    
    data = request.get_json()
    
    if 'obtained_date' in data:
        try:
            op_cert.obtained_date = datetime.strptime(data['obtained_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid obtained_date format'}), 400
    
    if 'expiry_date' in data:
        if data['expiry_date']:
            try:
                op_cert.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid expiry_date format'}), 400
        else:
            op_cert.expiry_date = None
    
    if 'status' in data:
        try:
            op_cert.status = CertificationStatus(data['status'])
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    if 'notes' in data:
        op_cert.notes = data['notes']
    
    op_cert.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'certification': op_cert.to_dict()}), 200


@operators_bp.route('/<int:operator_id>/certifications/<int:cert_id>', methods=['DELETE'])
@admin_required
def revoke_certification(operator_id, cert_id):
    """Revoke operator certification"""
    op_cert = OperatorCertification.query.filter_by(
        user_id=operator_id, certification_id=cert_id
    ).first()
    
    if not op_cert:
        return jsonify({'error': 'Certification not found'}), 404
    
    op_cert.status = CertificationStatus.REVOKED
    op_cert.updated_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'message': 'Certification revoked'}), 200


@operators_bp.route('/certifications', methods=['GET'])
@jwt_required()
def list_certifications():
    """List all certification types"""
    certs = Certification.query.filter_by(is_active=True).order_by(Certification.name).all()
    return jsonify({'certifications': [c.to_dict() for c in certs]}), 200


@operators_bp.route('/certifications', methods=['POST'])
@admin_required
def create_certification():
    """Create new certification type"""
    data = request.get_json()
    
    required = ['name', 'code']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if not validate_certification_code(data['code']):
        return jsonify({'error': 'Invalid certification code format'}), 400
    
    if Certification.query.filter_by(code=data['code'].upper()).first():
        return jsonify({'error': 'Certification code already exists'}), 400
    
    cert = Certification(
        name=data['name'],
        code=data['code'].upper(),
        level=data.get('level', 1),
        description=data.get('description'),
        validity_months=data.get('validity_months', 12)
    )
    
    db.session.add(cert)
    db.session.commit()
    
    return jsonify({'certification': cert.to_dict()}), 201


@operators_bp.route('/available-for-machine/<int:machine_id>', methods=['GET'])
@supervisor_required
def get_available_operators_for_machine(machine_id):
    """Get operators certified for a specific machine"""
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    # Get required certifications for machine type
    required_cert_ids = machine.machine_type.required_certifications or []
    
    if not required_cert_ids:
        # No specific certs required, return all active operators
        operators = User.query.filter_by(role=UserRole.OPERATOR, is_active=True).all()
    else:
        # Find operators with ALL required certifications
        subquery = db.session.query(OperatorCertification.user_id).filter(
            OperatorCertification.certification_id.in_(required_cert_ids),
            OperatorCertification.status == CertificationStatus.ACTIVE
        ).group_by(OperatorCertification.user_id).having(
            func.count(OperatorCertification.certification_id) == len(required_cert_ids)
        ).subquery()
        
        operators = User.query.filter(
            User.id.in_(subquery),
            User.role == UserRole.OPERATOR,
            User.is_active == True
        ).all()
    
    # Filter out operators already assigned to another machine in current/overlapping shift
    current_shift_id = request.args.get('shift_id', type=int)
    if current_shift_id:
        assigned_operator_ids = db.session.query(ShiftAssignment.operator_id).filter(
            ShiftAssignment.shift_id == current_shift_id,
            ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
        ).subquery()
        operators = [op for op in operators if op.id not in assigned_operator_ids]
    
    result = []
    for op in operators:
        op_data = op.to_dict()
        certs = OperatorCertification.query.filter_by(user_id=op.id, status=CertificationStatus.ACTIVE).all()
        op_data['certifications'] = [c.to_dict() for c in certs if c.is_valid()]
        result.append(op_data)
    
    return jsonify({'operators': result}), 200