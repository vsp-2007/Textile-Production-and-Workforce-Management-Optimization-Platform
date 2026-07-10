import click
from flask.cli import with_appcontext
from app import db
from app.models import (
    User, UserRole, Department, Machine, MachineType, MachineStatus,
    Certification, Shift, ShiftAssignment, AssignmentStatus
)
from werkzeug.security import generate_password_hash
from datetime import time, date, timedelta


def register_cli_commands(app):
    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Initialize database with tables and seed data"""
        click.echo('Creating database tables...')
        db.create_all()
        click.echo('Database tables created.')
        
        # Seed data
        seed_data()
        click.echo('Seed data inserted.')

    @app.cli.command('seed-db')
    @with_appcontext
    def seed_db():
        """Seed database with initial data"""
        seed_data()
        click.echo('Seed data inserted.')

    @app.cli.command('create-admin')
    @click.option('--employee-id', prompt=True, help='Employee ID')
    @click.option('--name', prompt=True, help='Full name')
    @click.option('--email', prompt=True, help='Email')
    @click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Password')
    @with_appcontext
    def create_admin(employee_id, name, email, password):
        """Create admin user"""
        if User.query.filter_by(employee_id=employee_id).first():
            click.echo('User already exists!')
            return
        
        user = User(
            employee_id=employee_id,
            name=name,
            email=email,
            role=UserRole.ADMIN
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user {employee_id} created.')

    @app.cli.command('reset-db')
    @click.confirmation_option(prompt='Are you sure you want to drop all tables?')
    @with_appcontext
    def reset_db():
        """Drop all tables and recreate"""
        db.drop_all()
        db.create_all()
        seed_data()
        click.echo('Database reset and seeded.')


def seed_data():
    """Seed database with initial data"""
    # Create departments
    departments = [
        {'name': 'Spinning', 'code': 'SPN'},
        {'name': 'Weaving', 'code': 'WVG'},
        {'name': 'Dyeing', 'code': 'DYE'},
        {'name': 'Finishing', 'code': 'FNS'},
        {'name': 'Quality Control', 'code': 'QC'},
        {'name': 'Maintenance', 'code': 'MNT'},
    ]
    
    for dept_data in departments:
        if not Department.query.filter_by(code=dept_data['code']).first():
            dept = Department(**dept_data)
            db.session.add(dept)
    
    db.session.commit()
    
    # Create machine types
    machine_types = [
        {
            'name': 'Ring Spinning Frame',
            'code': 'RSF',
            'description': 'Ring spinning machine for yarn production',
            'required_certifications': [],  # Will be set after certs created
            'default_capacity': 500,
            'maintenance_interval_hours': 8
        },
        {
            'name': 'Air Jet Loom',
            'code': 'AJL',
            'description': 'Air jet weaving loom',
            'required_certifications': [],
            'default_capacity': 200,
            'maintenance_interval_hours': 8
        },
        {
            'name': 'Rapier Loom',
            'code': 'RPL',
            'description': 'Rapier weaving loom',
            'required_certifications': [],
            'default_capacity': 180,
            'maintenance_interval_hours': 8
        },
        {
            'name': 'Jacquard Loom',
            'code': 'JQL',
            'description': 'Jacquard weaving loom for complex patterns',
            'required_certifications': [],
            'default_capacity': 120,
            'maintenance_interval_hours': 6
        },
        {
            'name': 'Winch Dyeing Machine',
            'code': 'WDM',
            'description': 'Winch dyeing for fabric',
            'required_certifications': [],
            'default_capacity': 1000,
            'maintenance_interval_hours': 12
        },
        {
            'name': 'Jet Dyeing Machine',
            'code': 'JDM',
            'description': 'High temperature jet dyeing',
            'required_certifications': [],
            'default_capacity': 800,
            'maintenance_interval_hours': 10
        },
        {
            'name': 'Stenter Frame',
            'code': 'STF',
            'description': 'Fabric finishing stenter',
            'required_certifications': [],
            'default_capacity': 1500,
            'maintenance_interval_hours': 8
        },
    ]
    
    for mt_data in machine_types:
        if not MachineType.query.filter_by(code=mt_data['code']).first():
            mt = MachineType(**mt_data)
            db.session.add(mt)
    
    db.session.commit()
    
    # Create certifications
    certifications = [
        {'name': 'Ring Spinning Operation', 'code': 'RSO', 'level': 1, 'validity_months': 12},
        {'name': 'Ring Spinning Operation', 'code': 'RSO', 'level': 2, 'validity_months': 12},
        {'name': 'Ring Spinning Operation', 'code': 'RSO', 'level': 3, 'validity_months': 12},
        {'name': 'Air Jet Loom Operation', 'code': 'AJL', 'level': 1, 'validity_months': 12},
        {'name': 'Air Jet Loom Operation', 'code': 'AJL', 'level': 2, 'validity_months': 12},
        {'name': 'Air Jet Loom Operation', 'code': 'AJL', 'level': 3, 'validity_months': 12},
        {'name': 'Rapier Loom Operation', 'code': 'RPL', 'level': 1, 'validity_months': 12},
        {'name': 'Rapier Loom Operation', 'code': 'RPL', 'level': 2, 'validity_months': 12},
        {'name': 'Jacquard Weaving', 'code': 'JQW', 'level': 1, 'validity_months': 12},
        {'name': 'Jacquard Weaving', 'code': 'JQW', 'level': 2, 'validity_months': 12},
        {'name': 'Jacquard Weaving', 'code': 'JQW', 'level': 3, 'validity_months': 12},
        {'name': 'Winch Dyeing Operation', 'code': 'WDO', 'level': 1, 'validity_months': 12},
        {'name': 'Jet Dyeing Operation', 'code': 'JDO', 'level': 1, 'validity_months': 12},
        {'name': 'Jet Dyeing Operation', 'code': 'JDO', 'level': 2, 'validity_months': 12},
        {'name': 'Stenter Operation', 'code': 'STO', 'level': 1, 'validity_months': 12},
        {'name': 'Machine Maintenance', 'code': 'MNT', 'level': 1, 'validity_months': 24},
        {'name': 'Quality Inspection', 'code': 'QCI', 'level': 1, 'validity_months': 12},
    ]
    
    cert_map = {}
    for cert_data in certifications:
        key = f"{cert_data['code']}_{cert_data['level']}"
        if not Certification.query.filter_by(code=cert_data['code'], level=cert_data['level']).first():
            cert = Certification(**cert_data)
            db.session.add(cert)
            cert_map[key] = cert
        else:
            cert_map[key] = Certification.query.filter_by(code=cert_data['code'], level=cert_data['level']).first()
    
    db.session.commit()
    
    # Update machine types with required certifications
    mt_certs = {
        'RSF': [('RSO', 1), ('RSO', 2)],
        'AJL': [('AJL', 1), ('AJL', 2)],
        'RPL': [('RPL', 1), ('RPL', 2)],
        'JQL': [('JQW', 2), ('JQW', 3)],
        'WDM': [('WDO', 1)],
        'JDM': [('JDO', 1), ('JDO', 2)],
        'STF': [('STO', 1)],
    }
    
    for code, certs in mt_certs.items():
        mt = MachineType.query.filter_by(code=code).first()
        if mt:
            cert_ids = []
            for c_code, level in certs:
                key = f"{c_code}_{level}"
                if key in cert_map:
                    cert_ids.append(cert_map[key].id)
            mt.required_certifications = cert_ids
    
    db.session.commit()
    
    # Create shifts
    shifts = [
        {'name': 'Morning Shift', 'code': 'MOR', 'start_time': '06:00', 'end_time': '14:00', 'rest_period_hours': 11},
        {'name': 'Evening Shift', 'code': 'EVE', 'start_time': '14:00', 'end_time': '22:00', 'rest_period_hours': 11},
        {'name': 'Night Shift', 'code': 'NIT', 'start_time': '22:00', 'end_time': '06:00', 'rest_period_hours': 11},
    ]
    
    for shift_data in shifts:
        if not Shift.query.filter_by(code=shift_data['code']).first():
            start_time = time.fromisoformat(shift_data['start_time'])
            end_time = time.fromisoformat(shift_data['end_time'])
            
            start_dt = datetime.combine(date.today(), start_time)
            end_dt = datetime.combine(date.today(), end_time)
            if end_dt <= start_dt:
                end_dt += timedelta(days=1)
            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            
            shift = Shift(
                name=shift_data['name'],
                code=shift_data['code'],
                start_time=start_time,
                end_time=end_time,
                duration_hours=duration_hours,
                rest_period_hours=shift_data['rest_period_hours']
            )
            db.session.add(shift)
    
    db.session.commit()
    
    # Create default admin user
    if not User.query.filter_by(employee_id='ADMIN001').first():
        admin = User(
            employee_id='ADMIN001',
            name='System Administrator',
            email='admin@texworkforce.com',
            role=UserRole.ADMIN,
            department_id=Department.query.filter_by(code='QC').first().id
        )
        admin.set_password('Admin@123')
        db.session.add(admin)
    
    # Create default supervisor
    if not User.query.filter_by(employee_id='SUPV001').first():
        supv = User(
            employee_id='SUPV001',
            name='Shift Supervisor',
            email='supervisor@texworkforce.com',
            role=UserRole.SUPERVISOR,
            department_id=Department.query.filter_by(code='WVG').first().id,
            shift_pattern='morning'
        )
        supv.set_password('Supervisor@123')
        db.session.add(supv)
    
    # Create sample operators
    operators = [
        {'employee_id': 'OPR001', 'name': 'John Doe', 'email': 'john.doe@texworkforce.com', 'dept': 'WVG', 'shift': 'morning'},
        {'employee_id': 'OPR002', 'name': 'Jane Smith', 'email': 'jane.smith@texworkforce.com', 'dept': 'WVG', 'shift': 'morning'},
        {'employee_id': 'OPR003', 'name': 'Mike Johnson', 'email': 'mike.johnson@texworkforce.com', 'dept': 'SPN', 'shift': 'evening'},
        {'employee_id': 'OPR004', 'name': 'Sarah Wilson', 'email': 'sarah.wilson@texworkforce.com', 'dept': 'SPN', 'shift': 'evening'},
        {'employee_id': 'OPR005', 'name': 'David Brown', 'email': 'david.brown@texworkforce.com', 'dept': 'DYE', 'shift': 'night'},
        {'employee_id': 'OPR006', 'name': 'Lisa Davis', 'email': 'lisa.davis@texworkforce.com', 'dept': 'DYE', 'shift': 'night'},
    ]
    
    for op_data in operators:
        if not User.query.filter_by(employee_id=op_data['employee_id']).first():
            dept = Department.query.filter_by(code=op_data['dept']).first()
            op = User(
                employee_id=op_data['employee_id'],
                name=op_data['name'],
                email=op_data['email'],
                role=UserRole.OPERATOR,
                department_id=dept.id if dept else None,
                shift_pattern=op_data['shift']
            )
            op.set_password('Operator@123')
            db.session.add(op)
    
    db.session.commit()
    
    # Assign certifications to operators
    cert_assignments = [
        ('OPR001', [('AJL', 2), ('RPL', 2)]),
        ('OPR002', [('JQW', 3), ('AJL', 1)]),
        ('OPR003', [('RSO', 3), ('RSO', 2)]),
        ('OPR004', [('RSO', 2), ('AJL', 1)]),
        ('OPR005', [('JDO', 2), ('WDO', 1)]),
        ('OPR006', [('STO', 1), ('JDO', 1)]),
    ]
    
    for emp_id, certs in cert_assignments:
        operator = User.query.filter_by(employee_id=emp_id).first()
        if operator:
            for c_code, level in certs:
                cert = Certification.query.filter_by(code=c_code, level=level).first()
                if cert:
                    existing = OperatorCertification.query.filter_by(
                        user_id=operator.id, certification_id=cert.id
                    ).first()
                    if not existing:
                        from datetime import date
                        from dateutil.relativedelta import relativedelta
                        op_cert = OperatorCertification(
                            user_id=operator.id,
                            certification_id=cert.id,
                            obtained_date=date.today() - relativedelta(months=6),
                            expiry_date=date.today() + relativedelta(months=6),
                            status=CertificationStatus.ACTIVE,
                            issued_by=1  # Admin
                        )
                        db.session.add(op_cert)
    
    db.session.commit()
    
    # Create sample machines
    machines = [
        {'code': 'RSF-01', 'name': 'Ring Spinning Frame 1', 'type': 'RSF', 'dept': 'SPN', 'zone': 'A', 'x': 100, 'y': 100},
        {'code': 'RSF-02', 'name': 'Ring Spinning Frame 2', 'type': 'RSF', 'dept': 'SPN', 'zone': 'A', 'x': 200, 'y': 100},
        {'code': 'RSF-03', 'name': 'Ring Spinning Frame 3', 'type': 'RSF', 'dept': 'SPN', 'zone': 'A', 'x': 300, 'y': 100},
        {'code': 'AJL-01', 'name': 'Air Jet Loom 1', 'type': 'AJL', 'dept': 'WVG', 'zone': 'B', 'x': 100, 'y': 300},
        {'code': 'AJL-02', 'name': 'Air Jet Loom 2', 'type': 'AJL', 'dept': 'WVG', 'zone': 'B', 'x': 200, 'y': 300},
        {'code': 'AJL-03', 'name': 'Air Jet Loom 3', 'type': 'AJL', 'dept': 'WVG', 'zone': 'B', 'x': 300, 'y': 300},
        {'code': 'RPL-01', 'name': 'Rapier Loom 1', 'type': 'RPL', 'dept': 'WVG', 'zone': 'B', 'x': 100, 'y': 400},
        {'code': 'RPL-02', 'name': 'Rapier Loom 2', 'type': 'RPL', 'dept': 'WVG', 'zone': 'B', 'x': 200, 'y': 400},
        {'code': 'JQL-01', 'name': 'Jacquard Loom 1', 'type': 'JQL', 'dept': 'WVG', 'zone': 'C', 'x': 100, 'y': 500},
        {'code': 'JQL-02', 'name': 'Jacquard Loom 2', 'type': 'JQL', 'dept': 'WVG', 'zone': 'C', 'x': 200, 'y': 500},
        {'code': 'WDM-01', 'name': 'Winch Dyeing 1', 'type': 'WDM', 'dept': 'DYE', 'zone': 'D', 'x': 100, 'y': 200},
        {'code': 'JDM-01', 'name': 'Jet Dyeing 1', 'type': 'JDM', 'dept': 'DYE', 'zone': 'D', 'x': 200, 'y': 200},
        {'code': 'STF-01', 'name': 'Stenter Frame 1', 'type': 'STF', 'dept': 'FNS', 'zone': 'E', 'x': 100, 'y': 100},
    ]
    
    for m_data in machines:
        if not Machine.query.filter_by(machine_code=m_data['code']).first():
            mt = MachineType.query.filter_by(code=m_data['type']).first()
            dept = Department.query.filter_by(code=m_data['dept']).first()
            
            machine = Machine(
                machine_code=m_data['code'],
                name=m_data['name'],
                machine_type_id=mt.id if mt else None,
                department_id=dept.id if dept else None,
                location_x=m_data['x'],
                location_y=m_data['y'],
                floor_zone=m_data['zone'],
                mqtt_topic=f"texworkforce/machines/{m_data['code']}/telemetry"
            )
            db.session.add(machine)
    
    db.session.commit()
    
    click.echo('Seed data completed successfully!')


# Import datetime at top level
from datetime import datetime, time, date, timedelta