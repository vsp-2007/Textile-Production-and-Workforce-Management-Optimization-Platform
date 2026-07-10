from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta

from app import db
from app.models import (
    Machine, MachineStatus, MachineStatus, MachineType,
    User, UserRole, Certification, OperatorCertification, CertificationStatus,
    Shift, ShiftAssignment, AssignmentStatus,
    Alert, AlertType, AlertSeverity
)
from app.utils.security import supervisor_required, admin_required
from app.services.reallocation_engine import find_reallocation_options, ReallocationEngine

reallocation_bp = Blueprint('reallocation', __name__)


@reallocation_bp.route('/recommend', methods=['POST'])
@supervisor_required
def recommend_reallocation():
    """Get reallocation recommendations for an idle operator"""
    data = request.get_json()
    
    required = ['operator_id', 'shift_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    operator = User.query.filter_by(id=data['operator_id'], role=UserRole.OPERATOR).first()
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    shift = Shift.query.get(data['shift_id'])
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    # Get machine that just went down (optional)
    broken_machine_id = data.get('machine_id')
    
    recommendations = find_reallocation_options(
        operator_id=data['operator_id'],
        shift_id=data['shift_id'],
        broken_machine_id=broken_machine_id
    )
    
    return jsonify({
        'operator_id': data['operator_id'],
        'shift_id': data['shift_id'],
        'recommendations': recommendations
    }), 200


@reallocation_bp.route('/approve', methods=['POST'])
@supervisor_required
def approve_reallocation():
    """Approve a reallocation recommendation"""
    data = request.get_json()
    
    required = ['operator_id', 'shift_id', 'new_machine_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    operator = User.query.filter_by(id=data['operator_id'], role=UserRole.OPERATOR).first()
    if not operator:
        return jsonify({'error': 'Operator not found'}), 404
    
    shift = Shift.query.get(data['shift_id'])
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    new_machine = Machine.query.get(data['new_machine_id'])
    if not new_machine:
        return jsonify({'error': 'Target machine not found'}), 404
    
    # Check if operator already assigned in this shift
    existing = ShiftAssignment.query.filter_by(
        shift_id=data['shift_id'],
        operator_id=data['operator_id'],
        status=AssignmentStatus.STARTED
    ).first()
    
    if existing:
        # Update existing assignment (reallocation)
        old_machine_id = existing.machine_id
        existing.machine_id = new_machine.id
        existing.status = AssignmentStatus.REASSIGNED
        existing.notes = f"Reallocated from machine {old_machine_id} - {data.get('reason', 'Machine fault')}"
        existing.updated_at = datetime.utcnow()
        
        # Update old machine status
        old_machine = Machine.query.get(old_machine_id)
        if old_machine:
            other_active = ShiftAssignment.query.filter(
                ShiftAssignment.machine_id == old_machine_id,
                ShiftAssignment.status == AssignmentStatus.STARTED,
                ShiftAssignment.id != existing.id
            ).count()
            if other_active == 0:
                old_machine.status = MachineStatus.IDLE
        
        # Update new machine status
        if new_machine.status == MachineStatus.IDLE:
            new_machine.status = MachineStatus.ACTIVE
        
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        socketio.emit('reallocation_approved', {
            'assignment': existing.to_dict(),
            'old_machine_id': old_machine_id,
            'new_machine_id': new_machine.id,
            'operator_id': data['operator_id']
        }, room='supervisors')
        
        return jsonify({'assignment': existing.to_dict(), 'message': 'Reallocation approved'}), 200
    else:
        # Create new assignment
        # Validate first
        from app.services.scheduler import validate_assignment
        is_valid, error = validate_assignment(data['shift_id'], new_machine.id, data['operator_id'])
        if not is_valid:
            return jsonify({'error': error}), 400
        
        supervisor_id = get_jwt_identity()
        assignment = ShiftAssignment(
            shift_id=data['shift_id'],
            machine_id=new_machine.id,
            operator_id=data['operator_id'],
            supervisor_id=supervisor_id,
            status=AssignmentStatus.STARTED,
            started_at=datetime.utcnow(),
            notes=f"Reallocated - {data.get('reason', 'Machine fault')}"
        )
        
        db.session.add(assignment)
        
        # Update new machine status
        if new_machine.status == MachineStatus.IDLE:
            new_machine.status = MachineStatus.ACTIVE
        
        db.session.commit()
        
        # Emit real-time update
        from app import socketio
        socketio.emit('reallocation_approved', {
            'assignment': assignment.to_dict(),
            'new_machine_id': new_machine.id,
            'operator_id': data['operator_id']
        }, room='supervisors')
        
        return jsonify({'assignment': assignment.to_dict(), 'message': 'Reallocation approved'}), 201


@reallocation_bp.route('/history', methods=['GET'])
@supervisor_required
def get_reallocation_history():
    """Get reallocation history"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    operator_id = request.args.get('operator_id', type=int)
    shift_id = request.args.get('shift_id', type=int)
    days = request.args.get('days', 30, type=int)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    query = ShiftAssignment.query.filter(
        ShiftAssignment.status == AssignmentStatus.REASSIGNED,
        ShiftAssignment.updated_at >= since
    )
    
    if operator_id:
        query = query.filter_by(operator_id=operator_id)
    
    if shift_id:
        query = query.filter_by(shift_id=shift_id)
    
    pagination = query.order_by(ShiftAssignment.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'reallocations': [r.to_dict() for r in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@reallocation_bp.route('/auto-suggest', methods=['POST'])
@supervisor_required
def auto_suggest_reallocation():
    """Automatically find and suggest reallocations for all idle operators due to machine faults"""
    data = request.get_json()
    shift_id = data.get('shift_id')
    
    if not shift_id:
        return jsonify({'error': 'shift_id required'}), 400
    
    shift = Shift.query.get(shift_id)
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
    
    # Find machines in fault/offline status with active assignments
    fault_machines = Machine.query.filter(
        Machine.status.in_([MachineStatus.FAULT, MachineStatus.OFFLINE]),
        Machine.is_active == True
    ).all()
    
    all_recommendations = []
    
    for machine in fault_machines:
        # Find active assignment for this machine in this shift
        assignment = ShiftAssignment.query.filter_by(
            shift_id=shift_id,
            machine_id=machine.id,
            status=AssignmentStatus.STARTED
        ).first()
        
        if assignment:
            # Operator is now idle, find alternatives
            recommendations = find_reallocation_options(
                operator_id=assignment.operator_id,
                shift_id=shift_id,
                broken_machine_id=machine.id
            )
            
            if recommendations:
                all_recommendations.append({
                    'operator_id': assignment.operator_id,
                    'operator_name': assignment.operator.name,
                    'broken_machine_id': machine.id,
                    'broken_machine_code': machine.machine_code,
                    'recommendations': recommendations
                })
    
    return jsonify({
        'shift_id': shift_id,
        'recommendations': all_recommendations
    }), 200