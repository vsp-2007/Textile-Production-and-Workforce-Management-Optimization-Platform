from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import enum


class UserRole(enum.Enum):
    ADMIN = 'admin'
    SUPERVISOR = 'supervisor'
    OPERATOR = 'operator'


class MachineStatus(enum.Enum):
    ACTIVE = 'active'
    IDLE = 'idle'
    MAINTENANCE = 'maintenance'
    FAULT = 'fault'
    OFFLINE = 'offline'
    DISCONNECTED = 'disconnected'


class ShiftStatus(enum.Enum):
    SCHEDULED = 'scheduled'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class AssignmentStatus(enum.Enum):
    ASSIGNED = 'assigned'
    STARTED = 'started'
    COMPLETED = 'completed'
    REASSIGNED = 'reassigned'
    CANCELLED = 'cancelled'


class CertificationStatus(enum.Enum):
    ACTIVE = 'active'
    EXPIRED = 'expired'
    REVOKED = 'revoked'
    PENDING = 'pending'


class AlertType(enum.Enum):
    MACHINE_FAULT = 'machine_fault'
    MACHINE_IDLE = 'machine_idle'
    MAINTENANCE_DUE = 'maintenance_due'
    OPERATOR_ABSENT = 'operator_absent'
    CERTIFICATION_EXPIRING = 'certification_expiring'
    SHIFT_VIOLATION = 'shift_violation'
    REALLOCATION_NEEDED = 'reallocation_needed'
    CONNECTION_LOST = 'connection_lost'


class AlertSeverity(enum.Enum):
    INFO = 'info'
    WARNING = 'warning'
    CRITICAL = 'critical'


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.OPERATOR)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    shift_pattern = db.Column(db.String(50), nullable=True)  # e.g., 'morning', 'evening', 'night'
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    department = db.relationship('Department', back_populates='users')
    certifications = db.relationship('OperatorCertification', back_populates='operator', cascade='all, delete-orphan')
    assigned_shifts = db.relationship('ShiftAssignment', foreign_keys='ShiftAssignment.operator_id', back_populates='operator')
    supervised_shifts = db.relationship('ShiftAssignment', foreign_keys='ShiftAssignment.supervisor_id', back_populates='supervisor')
    production_logs = db.relationship('ProductionLog', back_populates='operator')
    acknowledged_alerts = db.relationship('Alert', back_populates='acknowledged_by_user')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self, include_sensitive=False):
        data = {
            'id': self.id,
            'employee_id': self.employee_id,
            'name': self.name,
            'email': self.email,
            'role': self.role.value,
            'department_id': self.department_id,
            'shift_pattern': self.shift_pattern,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
        }
        if include_sensitive:
            data['failed_login_attempts'] = self.failed_login_attempts
            data['locked_until'] = self.locked_until.isoformat() if self.locked_until else None
        return data
    
    def __repr__(self):
        return f'<User {self.employee_id} - {self.name} ({self.role.value})>'


class Department(db.Model):
    __tablename__ = 'departments'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    users = db.relationship('User', back_populates='department')
    machines = db.relationship('Machine', back_populates='department')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'manager_id': self.manager_id,
            'created_at': self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<Department {self.code} - {self.name}>'


class MachineType(db.Model):
    __tablename__ = 'machine_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    required_certifications = db.Column(db.JSON, nullable=True)  # List of certification IDs
    default_capacity = db.Column(db.Integer, nullable=True)  # yards/hour
    maintenance_interval_hours = db.Column(db.Integer, default=8)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    machines = db.relationship('Machine', back_populates='machine_type')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'description': self.description,
            'required_certifications': self.required_certifications,
            'default_capacity': self.default_capacity,
            'maintenance_interval_hours': self.maintenance_interval_hours,
        }
    
    def __repr__(self):
        return f'<MachineType {self.code} - {self.name}>'


class Machine(db.Model):
    __tablename__ = 'machines'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    machine_type_id = db.Column(db.Integer, db.ForeignKey('machine_types.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=True)
    location_x = db.Column(db.Float, nullable=True)  # Floor map X coordinate
    location_y = db.Column(db.Float, nullable=True)  # Floor map Y coordinate
    floor_zone = db.Column(db.String(50), nullable=True)
    capacity_max = db.Column(db.Integer, nullable=True)  # yards/hour
    status = db.Column(db.Enum(MachineStatus), default=MachineStatus.OFFLINE, nullable=False, index=True)
    last_maintenance = db.Column(db.DateTime, nullable=True)
    maintenance_interval_hours = db.Column(db.Integer, default=8)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    mqtt_topic = db.Column(db.String(200), nullable=True)
    last_telemetry_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    machine_type = db.relationship('MachineType', back_populates='machines')
    department = db.relationship('Department', back_populates='machines')
    telemetry = db.relationship('MachineTelemetry', back_populates='machine', cascade='all, delete-orphan')
    downtimes = db.relationship('MachineDowntime', back_populates='machine', cascade='all, delete-orphan')
    assignments = db.relationship('ShiftAssignment', back_populates='machine')
    production_logs = db.relationship('ProductionLog', back_populates='machine')
    alerts = db.relationship('Alert', back_populates='machine')
    
    def to_dict(self, include_telemetry=False):
        data = {
            'id': self.id,
            'machine_code': self.machine_code,
            'name': self.name,
            'machine_type_id': self.machine_type_id,
            'machine_type': self.machine_type.to_dict() if self.machine_type else None,
            'department_id': self.department_id,
            'location_x': self.location_x,
            'location_y': self.location_y,
            'floor_zone': self.floor_zone,
            'capacity_max': self.capacity_max,
            'status': self.status.value,
            'last_maintenance': self.last_maintenance.isoformat() if self.last_maintenance else None,
            'maintenance_interval_hours': self.maintenance_interval_hours,
            'is_active': self.is_active,
            'last_telemetry_at': self.last_telemetry_at.isoformat() if self.last_telemetry_at else None,
            'created_at': self.created_at.isoformat(),
        }
        if include_telemetry and self.telemetry:
            latest = self.telemetry[-1]
            data['latest_telemetry'] = latest.to_dict()
        return data
    
    def __repr__(self):
        return f'<Machine {self.machine_code} - {self.name} ({self.status.value})>'


class Certification(db.Model):
    __tablename__ = 'certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    level = db.Column(db.Integer, default=1)
    description = db.Column(db.Text, nullable=True)
    validity_months = db.Column(db.Integer, default=12)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    operators = db.relationship('OperatorCertification', back_populates='certification')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'level': self.level,
            'description': self.description,
            'validity_months': self.validity_months,
            'is_active': self.is_active,
        }
    
    def __repr__(self):
        return f'<Certification {self.code} - {self.name} (L{self.level})>'


class OperatorCertification(db.Model):
    __tablename__ = 'operator_certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    certification_id = db.Column(db.Integer, db.ForeignKey('certifications.id'), nullable=False, index=True)
    obtained_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(CertificationStatus), default=CertificationStatus.ACTIVE, nullable=False)
    issued_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    operator = db.relationship('User', foreign_keys=[user_id], back_populates='certifications')
    certification = db.relationship('Certification', back_populates='operators')
    issuer = db.relationship('User', foreign_keys=[issued_by])
    
    def is_valid(self):
        if self.status != CertificationStatus.ACTIVE:
            return False
        if self.expiry_date and self.expiry_date < datetime.utcnow().date():
            return False
        return True
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'certification_id': self.certification_id,
            'certification': self.certification.to_dict() if self.certification else None,
            'obtained_date': self.obtained_date.isoformat(),
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'status': self.status.value,
            'is_valid': self.is_valid(),
            'issued_by': self.issued_by,
            'notes': self.notes,
        }
    
    def __repr__(self):
        return f'<OperatorCertification User:{self.user_id} Cert:{self.certification_id} ({self.status.value})>'


class Shift(db.Model):
    __tablename__ = 'shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    rest_period_hours = db.Column(db.Float, default=11)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    assignments = db.relationship('ShiftAssignment', back_populates='shift')
    reports = db.relationship('DailyReport', back_populates='shift')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_hours': self.duration_hours,
            'rest_period_hours': self.rest_period_hours,
            'is_active': self.is_active,
        }
    
    def __repr__(self):
        return f'<Shift {self.code} - {self.name} ({self.start_time}-{self.end_time})>'


class ShiftAssignment(db.Model):
    __tablename__ = 'shift_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False, index=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    status = db.Column(db.Enum(AssignmentStatus), default=AssignmentStatus.ASSIGNED, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime, nullable=True)
    ended_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    shift = db.relationship('Shift', back_populates='assignments')
    machine = db.relationship('Machine', back_populates='assignments')
    operator = db.relationship('User', foreign_keys=[operator_id], back_populates='assigned_shifts')
    supervisor = db.relationship('User', foreign_keys=[supervisor_id], back_populates='supervised_shifts')
    production_logs = db.relationship('ProductionLog', back_populates='assignment')
    
    # Composite index for conflict checking
    __table_args__ = (
        db.Index('ix_shift_operator_time', 'shift_id', 'operator_id'),
        db.Index('ix_shift_machine_time', 'shift_id', 'machine_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'shift_id': self.shift_id,
            'shift': self.shift.to_dict() if self.shift else None,
            'machine_id': self.machine_id,
            'machine': self.machine.to_dict() if self.machine else None,
            'operator_id': self.operator_id,
            'operator': self.operator.to_dict() if self.operator else None,
            'supervisor_id': self.supervisor_id,
            'supervisor': self.supervisor.to_dict() if self.supervisor else None,
            'status': self.status.value,
            'assigned_at': self.assigned_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'notes': self.notes,
        }
    
    def __repr__(self):
        return f'<ShiftAssignment Shift:{self.shift_id} Machine:{self.machine_id} Op:{self.operator_id} ({self.status.value})>'


class MachineTelemetry(db.Model):
    __tablename__ = 'machine_telemetry'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = db.Column(db.Enum(MachineStatus), nullable=False)
    rpm = db.Column(db.Float, nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    vibration = db.Column(db.Float, nullable=True)
    output_count = db.Column(db.Integer, nullable=True)  # yards produced
    error_code = db.Column(db.String(50), nullable=True)
    raw_payload = db.Column(db.JSON, nullable=True)
    
    machine = db.relationship('Machine', back_populates='telemetry')
    
    __table_args__ = (
        db.Index('ix_telemetry_machine_time', 'machine_id', 'timestamp'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'timestamp': self.timestamp.isoformat(),
            'status': self.status.value,
            'rpm': self.rpm,
            'temperature': self.temperature,
            'vibration': self.vibration,
            'output_count': self.output_count,
            'error_code': self.error_code,
            'raw_payload': self.raw_payload,
        }
    
    def __repr__(self):
        return f'<MachineTelemetry Machine:{self.machine_id} {self.status.value} at {self.timestamp}>'


class MachineDowntime(db.Model):
    __tablename__ = 'machine_downtime'
    
    id = db.Column(db.Integer, primary_key=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=True)
    reason = db.Column(db.String(200), nullable=False)
    reported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    machine = db.relationship('Machine', back_populates='downtimes')
    reporter = db.relationship('User', foreign_keys=[reported_by])
    resolver = db.relationship('User', foreign_keys=[resolved_by])
    
    def to_dict(self):
        return {
            'id': self.id,
            'machine_id': self.machine_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'reason': self.reason,
            'reported_by': self.reported_by,
            'resolved_by': self.resolved_by,
            'duration_minutes': self.duration_minutes,
        }
    
    def __repr__(self):
        return f'<MachineDowntime Machine:{self.machine_id} {self.start_time} - {self.end_time}>'


class ProductionLog(db.Model):
    __tablename__ = 'production_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    shift_assignment_id = db.Column(db.Integer, db.ForeignKey('shift_assignments.id'), nullable=False, index=True)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=False, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    target_yards = db.Column(db.Integer, nullable=True)
    actual_yards = db.Column(db.Integer, nullable=True)
    waste_yards = db.Column(db.Integer, default=0)
    quality_grade = db.Column(db.String(20), nullable=True)  # A, B, C, Reject
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    assignment = db.relationship('ShiftAssignment', back_populates='production_logs')
    machine = db.relationship('Machine', back_populates='production_logs')
    operator = db.relationship('User', back_populates='production_logs')
    
    @property
    def efficiency(self):
        if self.target_yards and self.target_yards > 0:
            return round((self.actual_yards or 0) / self.target_yards * 100, 2)
        return None
    
    @property
    def waste_percentage(self):
        if self.actual_yards and self.actual_yards > 0:
            return round(self.waste_yards / self.actual_yards * 100, 2)
        return None
    
    def to_dict(self):
        return {
            'id': self.id,
            'shift_assignment_id': self.shift_assignment_id,
            'machine_id': self.machine_id,
            'operator_id': self.operator_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'target_yards': self.target_yards,
            'actual_yards': self.actual_yards,
            'waste_yards': self.waste_yards,
            'quality_grade': self.quality_grade,
            'efficiency': self.efficiency,
            'waste_percentage': self.waste_percentage,
            'notes': self.notes,
        }
    
    def __repr__(self):
        return f'<ProductionLog Assignment:{self.shift_assignment_id} {self.actual_yards}/{self.target_yards} yds>'


class DailyReport(db.Model):
    __tablename__ = 'daily_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    report_date = db.Column(db.Date, nullable=False, index=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=False, index=True)
    total_machines = db.Column(db.Integer, default=0)
    active_machines = db.Column(db.Integer, default=0)
    total_operators = db.Column(db.Integer, default=0)
    present_operators = db.Column(db.Integer, default=0)
    total_yards = db.Column(db.Integer, default=0)
    total_waste = db.Column(db.Integer, default=0)
    avg_oee = db.Column(db.Float, nullable=True)
    downtime_minutes = db.Column(db.Integer, default=0)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    shift = db.relationship('Shift', back_populates='reports')
    
    __table_args__ = (
        db.UniqueConstraint('report_date', 'shift_id', name='uq_daily_report_date_shift'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'report_date': self.report_date.isoformat(),
            'shift_id': self.shift_id,
            'shift': self.shift.to_dict() if self.shift else None,
            'total_machines': self.total_machines,
            'active_machines': self.active_machines,
            'total_operators': self.total_operators,
            'present_operators': self.present_operators,
            'total_yards': self.total_yards,
            'total_waste': self.total_waste,
            'avg_oee': self.avg_oee,
            'downtime_minutes': self.downtime_minutes,
            'generated_at': self.generated_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<DailyReport {self.report_date} Shift:{self.shift_id}>'


class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.Enum(AlertType), nullable=False, index=True)
    severity = db.Column(db.Enum(AlertSeverity), default=AlertSeverity.WARNING, nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey('machines.id'), nullable=True, index=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    shift_id = db.Column(db.Integer, db.ForeignKey('shifts.id'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    machine = db.relationship('Machine', back_populates='alerts')
    operator = db.relationship('User', foreign_keys=[operator_id])
    shift = db.relationship('Shift')
    acknowledged_by_user = db.relationship('User', foreign_keys=[acknowledged_by], back_populates='acknowledged_alerts')
    
    def to_dict(self):
        return {
            'id': self.id,
            'alert_type': self.alert_type.value,
            'severity': self.severity.value,
            'machine_id': self.machine_id,
            'operator_id': self.operator_id,
            'shift_id': self.shift_id,
            'message': self.message,
            'is_read': self.is_read,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'created_at': self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<Alert {self.alert_type.value} [{self.severity.value}] Machine:{self.machine_id}>'


# Association table for user sessions (for concurrent session tracking)
class UserSession(db.Model):
    __tablename__ = 'user_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    device_info = db.Column(db.String(500), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    user = db.relationship('User')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'is_active': self.is_active,
        }
    
    def __repr__(self):
        return f'<UserSession User:{self.user_id} Active:{self.is_active}>'