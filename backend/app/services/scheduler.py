from datetime import datetime, date, timedelta, time
from sqlalchemy import and_, or_, func

from app import db
from app.models import (
    Shift, ShiftAssignment, AssignmentStatus, Machine, MachineStatus,
    User, UserRole, Certification, OperatorCertification, CertificationStatus
)


def validate_assignment(shift_id, machine_id, operator_id):
    """
    Validate if an operator can be assigned to a machine for a shift.
    Checks:
    1. Machine exists and is active
    2. Operator exists, is active, and has OPERATOR role
    3. Operator has required certifications for machine type
    4. Operator not double-booked in same shift
    5. Machine not already assigned in same shift
    6. Shift exists and is active
    7. Business rules: shift length, rest period
    """
    # Check shift
    shift = Shift.query.get(shift_id)
    if not shift:
        return False, 'Shift not found'
    if not shift.is_active:
        return False, 'Shift is not active'
    
    # Check machine
    machine = Machine.query.get(machine_id)
    if not machine:
        return False, 'Machine not found'
    if not machine.is_active:
        return False, 'Machine is not active'
    
    # Check operator
    operator = User.query.filter_by(id=operator_id, role=UserRole.OPERATOR).first()
    if not operator:
        return False, 'Operator not found'
    if not operator.is_active:
        return False, 'Operator is not active'
    
    # Check certifications
    required_cert_ids = machine.machine_type.required_certifications or []
    if required_cert_ids:
        operator_certs = OperatorCertification.query.filter(
            OperatorCertification.user_id == operator_id,
            OperatorCertification.certification_id.in_(required_cert_ids),
            OperatorCertification.status == CertificationStatus.ACTIVE
        ).all()
        
        valid_cert_ids = [c.certification_id for c in operator_certs if c.is_valid()]
        missing_certs = set(required_cert_ids) - set(valid_cert_ids)
        
        if missing_certs:
            missing_names = Certification.query.filter(Certification.id.in_(missing_certs)).all()
            missing_names_str = ', '.join([c.name for c in missing_names])
            return False, f'Operator missing required certifications: {missing_names_str}'
    
    # Check double-booking: operator already assigned in this shift
    existing_assignment = ShiftAssignment.query.filter(
        ShiftAssignment.shift_id == shift_id,
        ShiftAssignment.operator_id == operator_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
    ).first()
    
    if existing_assignment:
        return False, f'Operator already assigned to machine {existing_assignment.machine.machine_code} in this shift'
    
    # Check machine already assigned in this shift
    machine_assignment = ShiftAssignment.query.filter(
        ShiftAssignment.shift_id == shift_id,
        ShiftAssignment.machine_id == machine_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
    ).first()
    
    if machine_assignment:
        return False, f'Machine already assigned to operator {machine_assignment.operator.name} in this shift'
    
    # Check rest period (if operator has previous shift ending recently)
    # Find the last shift assignment for this operator that ended
    last_assignment = ShiftAssignment.query.filter(
        ShiftAssignment.operator_id == operator_id,
        ShiftAssignment.status == AssignmentStatus.COMPLETED,
        ShiftAssignment.ended_at != None
    ).order_by(ShiftAssignment.ended_at.desc()).first()
    
    if last_assignment and last_assignment.ended_at:
        rest_hours = (shift.start_time.replace(
            year=datetime.utcnow().year,
            month=datetime.utcnow().month,
            day=datetime.utcnow().day
        ) - last_assignment.ended_at).total_seconds() / 3600
        
        # Handle overnight shifts
        if rest_hours < 0:
            rest_hours += 24
        
        if rest_hours < shift.rest_period_hours:
            return False, f'Insufficient rest period: {rest_hours:.1f}h (minimum {shift.rest_period_hours}h required)'
    
    # Check shift duration limit (12 hours max)
    if shift.duration_hours > 12:
        return False, 'Shift exceeds maximum 12 hours'
    
    return True, None


def find_reallocation_options(operator_id, shift_id, broken_machine_id=None):
    """
    Find alternative machines for an idle operator.
    Returns list of recommendations with machine details and match score.
    """
    operator = User.query.filter_by(id=operator_id, role=UserRole.OPERATOR).first()
    if not operator:
        return []
    
    shift = Shift.query.get(shift_id)
    if not shift:
        return []
    
    # Get operator's valid certifications
    operator_certs = OperatorCertification.query.filter(
        OperatorCertification.user_id == operator_id,
        OperatorCertification.status == CertificationStatus.ACTIVE
    ).all()
    valid_cert_ids = set(c.certification_id for c in operator_certs if c.is_valid())
    
    # Get machines already assigned in this shift
    assigned_machine_ids = db.session.query(ShiftAssignment.machine_id).filter(
        ShiftAssignment.shift_id == shift_id,
        ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
    ).subquery()
    
    # Find available machines (active, not assigned, matching certifications)
    query = Machine.query.filter(
        Machine.is_active == True,
        Machine.status.in_([MachineStatus.ACTIVE, MachineStatus.IDLE]),
        ~Machine.id.in_(assigned_machine_ids)
    )
    
    if broken_machine_id:
        query = query.filter(Machine.id != broken_machine_id)
    
    available_machines = query.all()
    
    recommendations = []
    for machine in available_machines:
        required_cert_ids = set(machine.machine_type.required_certifications or [])
        
        # Check if operator has all required certifications
        if required_cert_ids.issubset(valid_cert_ids):
            # Calculate match score (100% if all certs match, partial otherwise)
            match_score = 100 if required_cert_ids else 50
            
            # Boost score for same machine type as broken machine
            if broken_machine_id:
                broken_machine = Machine.query.get(broken_machine_id)
                if broken_machine and broken_machine.machine_type_id == machine.machine_type_id:
                    match_score += 20
            
            # Boost for machines currently idle (higher priority)
            if machine.status == MachineStatus.IDLE:
                match_score += 10
            
            recommendations.append({
                'machine_id': machine.id,
                'machine_code': machine.machine_code,
                'machine_name': machine.name,
                'machine_type': machine.machine_type.name if machine.machine_type else 'Unknown',
                'floor_zone': machine.floor_zone,
                'location_x': machine.location_x,
                'location_y': machine.location_y,
                'current_status': machine.status.value,
                'match_score': min(match_score, 100),
                'required_certifications': [
                    Certification.query.get(cid).to_dict() for cid in required_cert_ids
                ] if required_cert_ids else []
            })
    
    # Sort by match score descending
    recommendations.sort(key=lambda x: x['match_score'], reverse=True)
    
    return recommendations


def get_operator_workload(operator_id, days=7):
    """Get operator's workload statistics"""
    since = datetime.utcnow() - timedelta(days=days)
    
    assignments = ShiftAssignment.query.filter(
        ShiftAssignment.operator_id == operator_id,
        ShiftAssignment.assigned_at >= since
    ).all()
    
    total_shifts = len(assignments)
    completed_shifts = len([a for a in assignments if a.status == AssignmentStatus.COMPLETED])
    total_hours = sum(a.shift.duration_hours for a in assignments if a.shift)
    
    return {
        'total_shifts': total_shifts,
        'completed_shifts': completed_shifts,
        'total_hours': total_hours,
        'avg_hours_per_shift': round(total_hours / total_shifts, 1) if total_shifts > 0 else 0
    }


def get_machine_utilization(machine_id, days=30):
    """Get machine utilization statistics"""
    since = datetime.utcnow() - timedelta(days=days)
    
    assignments = ShiftAssignment.query.filter(
        ShiftAssignment.machine_id == machine_id,
        ShiftAssignment.assigned_at >= since
    ).all()
    
    total_shifts = len(assignments)
    completed_shifts = len([a for a in assignments if a.status == AssignmentStatus.COMPLETED])
    
    # Get production data
    from app.models import ProductionLog
    logs = ProductionLog.query.filter(
        ProductionLog.machine_id == machine_id,
        ProductionLog.start_time >= since
    ).all()
    
    total_yards = sum(log.actual_yards or 0 for log in logs)
    total_target = sum(log.target_yards or 0 for log in logs)
    
    return {
        'total_shifts': total_shifts,
        'completed_shifts': completed_shifts,
        'total_yards': total_yards,
        'target_yards': total_target,
        'efficiency': round(total_yards / total_target * 100, 1) if total_target > 0 else 0
    }