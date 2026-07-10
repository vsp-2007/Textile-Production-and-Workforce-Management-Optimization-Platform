from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta, time

from app import db
from app.models import (
    Shift, ShiftAssignment, AssignmentStatus, Machine, MachineStatus,
    User, UserRole, Certification, OperatorCertification, CertificationStatus,
    Alert, AlertType, AlertSeverity
)
from app.utils.security import supervisor_required, admin_required
from app.services.scheduler import validate_assignment, find_reallocation_options

shifts_bp = Blueprint('shifts', __name__)


@shifts_bp.route('', methods=['GET'])
@jwt_required()
def list_shifts():
    """List all shifts"""
    shifts = Shift.query.filter_by(is_active=True).order_by(Shift.start_time).all()
    return jsonify({'shifts': [s.to_dict() for s in shifts]}), 200


@shifts_bp.route('', methods=['POST'])
@admin_required
def create_shift():
    """Create new shift"""
    data = request.get_json()
    
    required = ['name', 'code', 'start_time', 'end_time']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if Shift.query.filter_by(code=data['code'].upper()).first():
        return jsonify({'error': 'Shift code already exists'}), 400
    
    try:
        start_time = datetime.strptime(data['start_time'], '%H:%M').time()
        end_time = datetime.strptime(data['end_time'], '%H:%M').time()
    except ValueError:
        return jsonify({'error': 'Invalid time format (HH:MM)'}), 400
    
    # Calculate duration
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    duration_hours = (end_dt - start_dt).total_seconds() / 3600
    
    if duration_hours > 12:
        return jsonify({'error': 'Shift cannot exceed 12 hours'}), 400
    
    shift = Shift(
        name=data['name'],
        code=data['code'].upper(),
        start_time=start_time,
        end_time=end_time,
        duration_hours=duration_hours,
        rest_period_hours=data.get('rest_period_hours', 11)
    )
    
    db.session.add(shift)
    db.session.commit()
    
    return jsonify({'shift': shift.to_dict()}), 201


@shifts_bp.route('/<int:shift_id>', methods=['GET'])
@jwt_required()
def get_shift(shift_id):
    """Get shift with assignments"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    shift_data = shift.to_dict()
    
    # Get assignments for this shift
    assignments = ShiftAssignment.query.filter_by(shift_id=shift_id).all()
    shift_data['assignments'] = [a.to_dict() for a in assignments]
    
    return jsonify({'shift': shift_data}), 200


@shifts_bp.route('/<int:shift_id>/assignments', methods=['GET'])
@jwt_required()
def get_shift_assignments(shift_id):
    """Get all assignments for a shift"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    assignments = ShiftAssignment.query.filter_by(shift_id=shift_id).all()
    return jsonify({'assignments': [a.to_dict() for a in assignments]}), 200


@shifts_bp.route('/<int:shift_id>/assignments', methods=['POST'])
@supervisor_required
def create_assignment(shift_id):
    """Assign operator to machine for a shift"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    data = request.get_json()
    
    required = ['machine_id', 'operator_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    machine = Machine.query.get(data['machine_id'])
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    operator = User.query.filter_by(id=data['operator_id'], role=UserRole.OPERATOR).first()
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    supervisor_id = data.get('supervisor_id') or get_jwt_identity()
    supervisor = User.query.get(supervisor_id)
    if not supervisor or supervisor.role not in [UserRole.SUPERVISOR, UserRole.ADMIN]:
        return jsonify({'error': 'Invalid supervisor'}), 400
    
    # Validate assignment
    is_valid, error = validate_assignment(shift_id, machine.id, operator.id)
    if not is_valid:
        return jsonify({'error': error}), 400
    
    # Create assignment
    assignment = ShiftAssignment(
        shift_id=shift_id,
        machine_id=machine.id,
        operator_id=operator.id,
        supervisor_id=supervisor.id,
        status=AssignmentStatus.ASSIGNED,
        notes=data.get('notes')
    )
    
    db.session.add(assignment)
    
    # Update machine status to active if it was idle
    if machine.status == MachineStatus.IDLE:
        machine.status = MachineStatus.ACTIVE
    
    db.session.commit()
    
    # Emit real-time update
    from app import socketio
    socketio.emit('assignment_created', {
        'assignment': assignment.to_dict(),
        'shift_id': shift_id
    }, room='supervisors')
    
    return jsonify({'assignment': assignment.to_dict()}), 201


@shifts_bp.route('/assignments/<int:assignment_id>', methods=['PUT'])
@supervisor_required
def update_assignment(assignment_id):
    """Update shift assignment"""
    assignment = ShiftAssignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        try:
            new_status = AssignmentStatus(data['status'])
            assignment.status = new_status
            
            if new_status == AssignmentStatus.STARTED:
                assignment.started_at = datetime.utcnow()
            elif new_status in [AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED]:
                assignment.ended_at = datetime.utcnow()
        except ValueError:
            return jsonify({'error': 'Invalid status'}), 400
    
    if 'notes' in data:
        assignment.notes = data['notes']
    
    assignment.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Emit real-time update
    from app import socketio
    socketio.emit('assignment_updated', {
        'assignment': assignment.to_dict()
    }, room='supervisors')
    
    return jsonify({'assignment': assignment.to_dict()}), 200


@shifts_bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@supervisor_required
def delete_assignment(assignment_id):
    """Remove shift assignment"""
    assignment = ShiftAssignment.query.get(assignment_id)
    if not assignment:
        return jsonify({'error': 'Assignment not found'}), 404
    
    # Check if already started
    if assignment.status == AssignmentStatus.STARTED:
        return jsonify({'error': 'Cannot delete started assignment'}), 400
    
    machine_id = assignment.machine_id
    shift_id = assignment.shift_id
    
    db.session.delete(assignment)
    
    # Check if machine has other active assignments
    other_assignments = ShiftAssignment.query.filter(
        ShiftAssignment.machine_id == machine_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED]),
        ShiftAssignment.id != assignment_id
    ).count()
    
    if other_assignments == 0:
        machine = Machine.query.get(machine_id)
        if machine and machine.status == MachineStatus.ACTIVE:
            machine.status = MachineStatus.IDLE
    
    db.session.commit()
    
    # Emit real-time update
    from app import socketio
    socketio.emit('assignment_deleted', {
        'assignment_id': assignment_id,
        'shift_id': shift_id,
        'machine_id': machine_id
    }, room='supervisors')
    
    return jsonify({'message': 'Assignment removed'}), 200


@shifts_bp.route('/assignments/validate', methods=['POST'])
@supervisor_required
def validate_assignment_endpoint():
    """Validate if assignment is allowed (certifications, no double-booking)"""
    data = request.get_json()
    
    required = ['shift_id', 'machine_id', 'operator_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    is_valid, error = validate_assignment(
        data['shift_id'], data['machine_id'], data['operator_id']
    )
    
    if not is_valid:
        return jsonify({'valid': False, 'error': error}), 200
    
    # Get suggested alternatives if validation fails due to certifications
    alternatives = []
    if 'certification' in (error or '').lower():
        alternatives = find_reallocation_options(data['operator_id'], data['shift_id'])
    
    return jsonify({
        'valid': True,
        'alternatives': alternatives
    }), 200


@shifts_bp.route('/<int:shift_id>/unassigned-machines', methods=['GET'])
@supervisor_required
def get_unassigned_machines(shift_id):
    """Get machines not assigned in a shift"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    assigned_machine_ids = db.session.query(ShiftAssignment.machine_id).filter(
        ShiftAssignment.shift_id == shift_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
    ).subquery()
    
    machines = Machine.query.filter(
        Machine.is_active == True,
        ~Machine.id.in_(assigned_machine_ids)
    ).all()
    
    return jsonify({'machines': [m.to_dict() for m in machines]}), 200


@shifts_bp.route('/<int:shift_id>/available-operators', methods=['GET'])
@supervisor_required
def get_available_operators(shift_id):
    """Get operators available for a shift (not double-booked, certified)"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    machine_id = request.args.get('machine_id', type=int)
    
    # Get operators already assigned in this shift
    assigned_operator_ids = db.session.query(ShiftAssignment.operator_id).filter(
        ShiftAssignment.shift_id == shift_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
    ).subquery()
    
    # Base query: active operators not assigned in this shift
    query = User.query.filter(
        User.role == UserRole.OPERATOR,
        User.is_active == True,
        ~User.id.in_(assigned_operator_ids)
    )
    
    # If machine specified, filter by certifications
    if machine_id:
        machine = Machine.query.get(machine_id)
        if machine:
            required_cert_ids = machine.machine_type.required_certifications or []
            if required_cert_ids:
                subquery = db.session.query(OperatorCertification.user_id).filter(
                    OperatorCertification.certification_id.in_(required_cert_ids),
                    OperatorCertification.status == CertificationStatus.ACTIVE
                ).group_by(OperatorCertification.user_id).having(
                    func.count(OperatorCertification.certification_id) == len(required_cert_ids)
                ).subquery()
                query = query.filter(User.id.in_(subquery))
    
    operators = query.all()
    
    result = []
    for op in operators:
        op_data = op.to_dict()
        certs = OperatorCertification.query.filter_by(
            user_id=op.id, status=CertificationStatus.ACTIVE
        ).all()
        op_data['certifications'] = [c.to_dict() for c in certs if c.is_valid()]
        result.append(op_data)
    
    return jsonify({'operators': result}), 200


@shifts_bp.route('/today', methods=['GET'])
@jwt_required()
def get_today_shifts():
    """Get today's shifts with assignments"""
    today = date.today()
    
    shifts = Shift.query.filter_by(is_active=True).all()
    
    result = []
    for shift in shifts:
        shift_data = shift.to_dict()
        assignments = ShiftAssignment.query.filter_by(shift_id=shift.id).all()
        shift_data['assignments'] = [a.to_dict() for a in assignments]
        result.append(shift_data)
    
    return jsonify({'shifts': result}), 200


@shifts_bp.route('/<int:shift_id>/start', methods=['POST'])
@supervisor_required
def start_shift(shift_id):
    """Start a shift - mark all assignments as started"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    assignments = ShiftAssignment.query.filter_by(
        shift_id=shift_id, status=AssignmentStatus.ASSIGNED
    ).all()
    
    for assignment in assignments:
        assignment.status = AssignmentStatus.STARTED
        assignment.started_at = datetime.utcnow()
        
        # Update machine status
        machine = Machine.query.get(assignment.machine_id)
        if machine and machine.status == MachineStatus.IDLE:
            machine.status = MachineStatus.ACTIVE
    
    db.session.commit()
    
    # Emit real-time update
    from app import socketio
    socketio.emit('shift_started', {
        'shift_id': shift_id,
        'assignments': [a.to_dict() for a in assignments]
    }, room='supervisors')
    
    return jsonify({'message': f'Shift started with {len(assignments)} assignments'}), 200


@shifts_bp.route('/<int:shift_id>/end', methods=['POST'])
@supervisor_required
def end_shift(shift_id):
    """End a shift - mark all assignments as completed"""
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    assignments = ShiftAssignment.query.filter_by(
        shift_id=shift_id, status=AssignmentStatus.STARTED
    ).all()
    
    for assignment in assignments:
        assignment.status = AssignmentStatus.COMPLETED
        assignment.ended_at = datetime.utcnow()
        
        # Update machine status
        machine = Machine.query.get(assignment.machine_id)
        if machine and machine.status == MachineStatus.ACTIVE:
            # Check if machine has other active assignments
            other_active = ShiftAssignment.query.filter(
                ShiftAssignment.machine_id == assignment.machine_id,
                ShiftAssignment.status == AssignmentStatus.STARTED,
                ShiftAssignment.id != assignment.id
            ).count()
            if other_active == 0:
                machine.status = MachineStatus.IDLE
    
    db.session.commit()
    
    # Trigger report generation
    from app.services.report_generator import generate_daily_report
    generate_daily_report.delay(shift_id, date.today().isoformat())
    
    # Emit real-time update
    from app import socketio
    socketio.emit('shift_ended', {
        'shift_id': shift_id,
        'assignments': [a.to_dict() for a in assignments]
    }, room='supervisors')
    
    return jsonify({'message': f'Shift ended, {len(assignments)} assignments completed'}), 200