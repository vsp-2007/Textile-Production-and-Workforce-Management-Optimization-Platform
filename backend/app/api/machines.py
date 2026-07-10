from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import or_, and_, func
from datetime import datetime, date, timedelta

from app import db
from app.models import (
    Machine, MachineType, MachineStatus, MachineTelemetry, MachineDowntime,
    User, UserRole, Department, Shift, ShiftAssignment, AssignmentStatus,
    Alert, AlertType, AlertSeverity
)
from app.utils.security import supervisor_required, admin_required, validate_machine_code
from app.services.mqtt_client import mqtt_client

machines_bp = Blueprint('machines', __name__)


@machines_bp.route('', methods=['GET'])
@jwt_required()
def list_machines():
    """List all machines with filters"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status_filter = request.args.get('status')
    type_filter = request.args.get('type_id', type=int)
    department_filter = request.args.get('department_id', type=int)
    zone_filter = request.args.get('zone')
    search = request.args.get('search', '')
    include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'
    
    query = Machine.query
    
    if not include_inactive:
        query = query.filter_by(is_active=True)
    
    if status_filter:
        try:
            query = query.filter_by(status=MachineStatus(status_filter))
        except ValueError:
            pass
    
    if type_filter:
        query = query.filter_by(machine_type_id=type_filter)
    
    if department_filter:
        query = query.filter_by(department_id=department_filter)
    
    if zone_filter:
        query = query.filter_by(floor_zone=zone_filter)
    
    if search:
        query = query.filter(
            or_(
                Machine.machine_code.ilike(f'%{search}%'),
                Machine.name.ilike(f'%{search}%')
            )
        )
    
    pagination = query.order_by(Machine.machine_code).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'machines': [m.to_dict() for m in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@machines_bp.route('/<int:machine_id>', methods=['GET'])
@jwt_required()
def get_machine(machine_id):
    """Get machine details with latest telemetry"""
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    include_telemetry = request.args.get('include_telemetry', 'true').lower() == 'true'
    return jsonify({'machine': machine.to_dict(include_telemetry=include_telemetry)}), 200


@machines_bp.route('', methods=['POST'])
@admin_required
def create_machine():
    """Register new machine"""
    data = request.get_json()
    
    required = ['machine_code', 'name', 'machine_type_id']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if not validate_machine_code(data['machine_code']):
        return jsonify({'error': 'Invalid machine code format'}), 400
    
    if Machine.query.filter_by(machine_code=data['machine_code'].upper()).first():
        return jsonify({'error': 'Machine code already exists'}), 400
    
    machine_type = MachineType.query.get(data['machine_type_id'])
    if not machine_type:
        return jsonify({'error': 'Machine type not found'}), 404
    
    machine = Machine(
        machine_code=data['machine_code'].upper(),
        name=data['name'],
        machine_type_id=data['machine_type_id'],
        department_id=data.get('department_id'),
        location_x=data.get('location_x'),
        location_y=data.get('location_y'),
        floor_zone=data.get('floor_zone'),
        capacity_max=data.get('capacity_max') or machine_type.default_capacity,
        maintenance_interval_hours=data.get('maintenance_interval_hours') or machine_type.maintenance_interval_hours,
        mqtt_topic=data.get('mqtt_topic') or f"texworkforce/machines/{data['machine_code'].upper()}"
    )
    
    db.session.add(machine)
    db.session.commit()
    
    return jsonify({'machine': machine.to_dict()}), 201


@machines_bp.route('/<int:machine_id>', methods=['PUT'])
@admin_required
def update_machine(machine_id):
    """Update machine configuration"""
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        machine.name = data['name']
    if 'machine_type_id' in data:
        mt = MachineType.query.get(data['machine_type_id'])
        if not mt:
            return jsonify({'error': 'Machine type not found'}), 404
        machine.machine_type_id = data['machine_type_id']
    if 'department_id' in data:
        machine.department_id = data['department_id']
    if 'location_x' in data:
        machine.location_x = data['location_x']
    if 'location_y' in data:
        machine.location_y = data['location_y']
    if 'floor_zone' in data:
        machine.floor_zone = data['floor_zone']
    if 'capacity_max' in data:
        machine.capacity_max = data['capacity_max']
    if 'maintenance_interval_hours' in data:
        machine.maintenance_interval_hours = data['maintenance_interval_hours']
    if 'mqtt_topic' in data:
        machine.mqtt_topic = data['mqtt_topic']
    if 'is_active' in data:
        machine.is_active = data['is_active']
    
    db.session.commit()
    
    return jsonify({'machine': machine.to_dict()}), 200


@machines_bp.route('/<int:machine_id>/status', methods=['PUT'])
@jwt_required()
def update_machine_status(machine_id):
    """Update machine status (IoT or Supervisor)"""
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')
    
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'error': 'Status required'}), 400
    
    try:
        status = MachineStatus(new_status)
    except ValueError:
        return jsonify({'error': 'Invalid status'}), 400
    
    # Only system/IoT or supervisor can change to fault/maintenance
    if status in [MachineStatus.FAULT, MachineStatus.MAINTENANCE]:
        if user_role not in [UserRole.SUPERVISOR.value, UserRole.ADMIN.value, 'system']:
            return jsonify({'error': 'Insufficient permissions for this status'}), 403
    
    old_status = machine.status
    machine.status = status
    
    # Create telemetry record
    telemetry = MachineTelemetry(
        machine_id=machine.id,
        status=status,
        rpm=data.get('rpm'),
        temperature=data.get('temperature'),
        vibration=data.get('vibration'),
        output_count=data.get('output_count'),
        error_code=data.get('error_code'),
        raw_payload=data.get('raw_payload')
    )
    db.session.add(telemetry)
    
    # Handle downtime tracking
    if old_status == MachineStatus.ACTIVE and status in [MachineStatus.FAULT, MachineStatus.OFFLINE, MachineStatus.MAINTENANCE]:
        downtime = MachineDowntime(
            machine_id=machine.id,
            start_time=datetime.utcnow(),
            reason=data.get('reason') or f'Status changed to {status.value}',
            reported_by=get_jwt_identity()
        )
        db.session.add(downtime)
    elif old_status in [MachineStatus.FAULT, MachineStatus.OFFLINE, MachineStatus.MAINTENANCE] and status == MachineStatus.ACTIVE:
        # Close open downtime
        open_downtime = MachineDowntime.query.filter_by(
            machine_id=machine.id, end_time=None
        ).first()
        if open_downtime:
            open_downtime.end_time = datetime.utcnow()
            open_downtime.resolved_by = get_jwt_identity()
            open_downtime.duration_minutes = int(
                (open_downtime.end_time - open_downtime.start_time).total_seconds() / 60
            )
    
    # Create alert for faults
    if status == MachineStatus.FAULT:
        alert = Alert(
            alert_type=AlertType.MACHINE_FAULT,
            severity=AlertSeverity.CRITICAL,
            machine_id=machine.id,
            message=f'Machine {machine.machine_code} ({machine.name}) reported fault: {data.get("error_code", "Unknown error")}'
        )
        db.session.add(alert)
    elif status == MachineStatus.IDLE:
        alert = Alert(
            alert_type=AlertType.MACHINE_IDLE,
            severity=AlertSeverity.WARNING,
            machine_id=machine.id,
            message=f'Machine {machine.machine_code} ({machine.name}) is idle (no operator assigned)'
        )
        db.session.add(alert)
    
    machine.last_telemetry_at = datetime.utcnow()
    db.session.commit()
    
    # Emit real-time update
    from app import socketio
    socketio.emit('machine_status_update', {
        'machine_id': machine.id,
        'machine_code': machine.machine_code,
        'name': machine.name,
        'status': status.value,
        'timestamp': datetime.utcnow().isoformat(),
        'telemetry': telemetry.to_dict()
    }, room='supervisors')
    
    return jsonify({'machine': machine.to_dict(include_telemetry=True)}), 200


@machines_bp.route('/<int:machine_id>/telemetry', methods=['GET'])
@jwt_required()
def get_machine_telemetry(machine_id):
    """Get machine telemetry history"""
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 50, type=int), 200)
    hours = request.args.get('hours', 24, type=int)
    
    since = datetime.utcnow() - timedelta(hours=hours)
    
    query = MachineTelemetry.query.filter(
        MachineTelemetry.machine_id == machine_id,
        MachineTelemetry.timestamp >= since
    ).order_by(MachineTelemetry.timestamp.desc())
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'telemetry': [t.to_dict() for t in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@machines_bp.route('/<int:machine_id>/downtime', methods=['GET'])
@jwt_required()
def get_machine_downtime(machine_id):
    """Get machine downtime history"""
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    
    query = MachineDowntime.query.filter_by(machine_id=machine_id).order_by(
        MachineDowntime.start_time.desc()
    )
    
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'downtimes': [d.to_dict() for d in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages
    }), 200


@machines_bp.route('/types', methods=['GET'])
@jwt_required()
def list_machine_types():
    """List all machine types"""
    types = MachineType.query.filter_by(is_active=True).all()
    return jsonify({'machine_types': [t.to_dict() for t in types]}), 200


@machines_bp.route('/types', methods=['POST'])
@admin_required
def create_machine_type():
    """Create new machine type"""
    data = request.get_json()
    
    required = ['name', 'code']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    if MachineType.query.filter_by(code=data['code'].upper()).first():
        return jsonify({'error': 'Machine type code already exists'}), 400
    
    mt = MachineType(
        name=data['name'],
        code=data['code'].upper(),
        description=data.get('description'),
        required_certifications=data.get('required_certifications'),
        default_capacity=data.get('default_capacity'),
        maintenance_interval_hours=data.get('maintenance_interval_hours', 8)
    )
    
    db.session.add(mt)
    db.session.commit()
    
    return jsonify({'machine_type': mt.to_dict()}), 201


@machines_bp.route('/floor-map', methods=['GET'])
@jwt_required()
def get_floor_map():
    """Get all machines with positions for floor map visualization"""
    machines = Machine.query.filter_by(is_active=True).all()
    
    zones = {}
    for m in machines:
        zone = m.floor_zone or 'General'
        if zone not in zones:
            zones[zone] = []
        zones[zone].append(m.to_dict())
    
    return jsonify({
        'zones': zones,
        'machines': [m.to_dict() for m in machines]
    }), 200


@machines_bp.route('/stats/summary', methods=['GET'])
@supervisor_required
def get_machine_stats():
    """Get machine statistics summary"""
    total = Machine.query.filter_by(is_active=True).count()
    active = Machine.query.filter_by(is_active=True, status=MachineStatus.ACTIVE).count()
    idle = Machine.query.filter_by(is_active=True, status=MachineStatus.IDLE).count()
    maintenance = Machine.query.filter_by(is_active=True, status=MachineStatus.MAINTENANCE).count()
    fault = Machine.query.filter_by(is_active=True, status=MachineStatus.FAULT).count()
    offline = Machine.query.filter_by(is_active=True, status=MachineStatus.OFFLINE).count()
    disconnected = Machine.query.filter_by(is_active=True, status=MachineStatus.DISCONNECTED).count()
    
    # OEE calculation (simplified)
    # OEE = Availability × Performance × Quality
    # For now, return basic stats
    
    return jsonify({
        'total': total,
        'active': active,
        'idle': idle,
        'maintenance': maintenance,
        'fault': fault,
        'offline': offline,
        'disconnected': disconnected,
        'utilization': round(active / total * 100, 1) if total > 0 else 0
    }), 200