from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta, time
import io
import csv

from app import db
from app.models import (
    DailyReport, Shift, ShiftAssignment, AssignmentStatus,
    ProductionLog, Machine, MachineDowntime, MachineStatus,
    User, UserRole, Alert, AlertType, AlertSeverity
)
from app.utils.security import supervisor_required, admin_required
from app.services.report_generator import (
    generate_daily_report_data, generate_shift_report_data,
    generate_machine_report_data, generate_operator_report_data,
    export_report_pdf, export_report_excel
)

reports_bp = Blueprint('reports', __name__)


@reports_bp.route('/daily', methods=['GET'])
@supervisor_required
def get_daily_report():
    """Get daily production report"""
    report_date = request.args.get('date')
    shift_id = request.args.get('shift_id', type=int)
    
    if report_date:
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format (YYYY-MM-DD)'}), 400
    else:
        report_date = date.today()
    
    # Try to get existing report
    query = DailyReport.query.filter_by(report_date=report_date)
    if shift_id:
        query = query.filter_by(shift_id=shift_id)
    
    reports = query.all()
    
    if reports:
        return jsonify({'reports': [r.to_dict() for r in reports]}), 200
    
    # Generate new report
    if shift_id:
        report_data = generate_shift_report_data(shift_id, report_date)
        return jsonify({'report': report_data}), 200
    else:
        # Generate for all shifts
        shifts = Shift.query.filter_by(is_active=True).all()
        all_reports = []
        for shift in shifts:
            report_data = generate_shift_report_data(shift.id, report_date)
            all_reports.append(report_data)
        return jsonify({'reports': all_reports}), 200


@reports_bp.route('/shift/<int:shift_id>', methods=['GET'])
@supervisor_required
def get_shift_report(shift_id):
    """Get shift-specific report"""
    report_date = request.args.get('date')
    
    if report_date:
        try:
            report_date = datetime.strptime(report_date, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format (YYYY-MM-DD)'}), 400
    else:
        report_date = date.today()
    
    report_data = generate_shift_report_data(shift_id, report_date)
    return jsonify({'report': report_data}), 200


@reports_bp.route('/machine/<int:machine_id>', methods=['GET'])
@supervisor_required
def get_machine_report(machine_id):
    """Get machine performance report"""
    days = request.args.get('days', 30, type=int)
    report_data = generate_machine_report_data(machine_id, days)
    return jsonify({'report': report_data}), 200


@reports_bp.route('/operator/<int:operator_id>', methods=['GET'])
@supervisor_required
def get_operator_report(operator_id):
    """Get operator productivity report"""
    days = request.args.get('days', 30, type=int)
    report_data = generate_operator_report_data(operator_id, days)
    return jsonify({'report': report_data}), 200


@reports_bp.route('/export', methods=['POST'])
@supervisor_required
def export_report():
    """Export report as PDF or Excel"""
    data = request.get_json()
    
    report_type = data.get('type')  # daily, shift, machine, operator
    format = data.get('format', 'pdf')  # pdf, excel
    params = data.get('params', {})
    
    if report_type == 'daily':
        report_date = params.get('date', date.today().isoformat())
        shift_id = params.get('shift_id')
        
        if shift_id:
            report_data = generate_shift_report_data(shift_id, report_date)
            filename = f"shift_report_{shift_id}_{report_date}"
        else:
            shifts = Shift.query.filter_by(is_active=True).all()
            report_data = {'shifts': []}
            for shift in shifts:
                report_data['shifts'].append(generate_shift_report_data(shift.id, report_date))
            filename = f"daily_report_{report_date}"
    
    elif report_type == 'shift':
        shift_id = params.get('shift_id')
        report_date = params.get('date', date.today().isoformat())
        report_data = generate_shift_report_data(shift_id, report_date)
        filename = f"shift_report_{shift_id}_{report_date}"
    
    elif report_type == 'machine':
        machine_id = params.get('machine_id')
        days = params.get('days', 30)
        report_data = generate_machine_report_data(machine_id, days)
        filename = f"machine_report_{machine_id}_{days}d"
    
    elif report_type == 'operator':
        operator_id = params.get('operator_id')
        days = params.get('days', 30)
        report_data = generate_operator_report_data(operator_id, days)
        filename = f"operator_report_{operator_id}_{days}d"
    
    else:
        return jsonify({'error': 'Invalid report type'}), 400
    
    if format == 'pdf':
        pdf_buffer = export_report_pdf(report_data, report_type)
        return send_file(
            pdf_buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"{filename}.pdf"
        )
    elif format == 'excel':
        excel_buffer = export_report_excel(report_data, report_type)
        return send_file(
            excel_buffer,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f"{filename}.xlsx"
        )
    else:
        return jsonify({'error': 'Invalid format'}), 400


@reports_bp.route('/oee/<int:machine_id>', methods=['GET'])
@supervisor_required
def get_machine_oee(machine_id):
    """Get OEE (Overall Equipment Effectiveness) for a machine"""
    days = request.args.get('days', 30, type=int)
    
    machine = Machine.query.get(machine_id)
    if not machine:
        return jsonify({'error': 'Machine not found'}), 404
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Get production logs for this machine
    logs = ProductionLog.query.filter(
        ProductionLog.machine_id == machine_id,
        ProductionLog.start_time >= since
    ).all()
    
    # Get downtime
    downtimes = MachineDowntime.query.filter(
        MachineDowntime.machine_id == machine_id,
        MachineDowntime.start_time >= since
    ).all()
    
    # Calculate OEE components
    # Availability = Operating Time / Planned Production Time
    # Performance = (Total Count / Ideal Run Rate) / Operating Time
    # Quality = Good Count / Total Count
    # OEE = Availability × Performance × Quality
    
    planned_time_hours = days * 24  # Simplified
    operating_time_hours = sum(
        (log.end_time - log.start_time).total_seconds() / 3600
        for log in logs if log.end_time
    )
    downtime_hours = sum(d.duration_minutes or 0 for d in downtimes) / 60
    
    availability = (operating_time_hours / planned_time_hours * 100) if planned_time_hours > 0 else 0
    
    total_yards = sum(log.actual_yards or 0 for log in logs)
    target_yards = sum(log.target_yards or 0 for log in logs)
    performance = (total_yards / target_yards * 100) if target_yards > 0 else 0
    
    good_yards = sum(log.actual_yards or 0 for log in logs if log.quality_grade in ['A', 'B'])
    quality = (good_yards / total_yards * 100) if total_yards > 0 else 0
    
    oee = (availability * performance * quality) / 10000
    
    return jsonify({
        'machine_id': machine_id,
        'machine_code': machine.machine_code,
        'period_days': days,
        'oee': round(oee, 2),
        'availability': round(availability, 2),
        'performance': round(performance, 2),
        'quality': round(quality, 2),
        'planned_time_hours': planned_time_hours,
        'operating_time_hours': round(operating_time_hours, 2),
        'downtime_hours': round(downtime_hours, 2),
        'total_yards': total_yards,
        'target_yards': target_yards,
        'good_yards': good_yards
    }), 200


@reports_bp.route('/summary', methods=['GET'])
@supervisor_required
def get_production_summary():
    """Get production summary for dashboard"""
    days = request.args.get('days', 7, type=int)
    shift_id = request.args.get('shift_id', type=int)
    
    since = datetime.utcnow() - timedelta(days=days)
    
    # Base query for production logs
    query = ProductionLog.query.filter(ProductionLog.start_time >= since)
    
    if shift_id:
        query = query.join(ShiftAssignment).filter(ShiftAssignment.shift_id == shift_id)
    
    logs = query.all()
    
    total_yards = sum(log.actual_yards or 0 for log in logs)
    total_waste = sum(log.waste_yards or 0 for log in logs)
    total_target = sum(log.target_yards or 0 for log in logs)
    
    # By day
    daily_data = {}
    for log in logs:
        day_key = log.start_time.date().isoformat()
        if day_key not in daily_data:
            daily_data[day_key] = {'yards': 0, 'waste': 0, 'target': 0, 'count': 0}
        daily_data[day_key]['yards'] += log.actual_yards or 0
        daily_data[day_key]['waste'] += log.waste_yards or 0
        daily_data[day_key]['target'] += log.target_yards or 0
        daily_data[day_key]['count'] += 1
    
    daily_list = [
        {'date': k, **v, 'efficiency': round(v['yards'] / v['target'] * 100, 1) if v['target'] > 0 else 0}
        for k, v in sorted(daily_data.items())
    ]
    
    # By machine
    machine_data = {}
    for log in logs:
        mid = log.machine_id
        if mid not in machine_data:
            machine_data[mid] = {'yards': 0, 'waste': 0, 'target': 0}
        machine_data[mid]['yards'] += log.actual_yards or 0
        machine_data[mid]['waste'] += log.waste_yards or 0
        machine_data[mid]['target'] += log.target_yards or 0
    
    machines = Machine.query.filter(Machine.id.in_(machine_data.keys())).all()
    machine_list = []
    for m in machines:
        d = machine_data[m.id]
        machine_list.append({
            'machine_id': m.id,
            'machine_code': m.machine_code,
            'name': m.name,
            'yards': d['yards'],
            'waste': d['waste'],
            'target': d['target'],
            'efficiency': round(d['yards'] / d['target'] * 100, 1) if d['target'] > 0 else 0
        })
    
    return jsonify({
        'period_days': days,
        'total_yards': total_yards,
        'total_waste': total_waste,
        'total_target': total_target,
        'overall_efficiency': round(total_yards / total_target * 100, 1) if total_target > 0 else 0,
        'waste_percentage': round(total_waste / total_yards * 100, 1) if total_yards > 0 else 0,
        'daily': daily_list,
        'by_machine': machine_list
    }), 200