"""
Reallocation Engine - Advanced workforce reallocation algorithms
"""

from datetime import datetime, date, timedelta
from sqlalchemy import and_, or_, func
from collections import defaultdict

from app import db
from app.models import (
    Machine, MachineStatus, MachineType,
    User, UserRole, Certification, OperatorCertification, CertificationStatus,
    Shift, ShiftAssignment, AssignmentStatus,
    Alert, AlertType, AlertSeverity
)
from app.services.scheduler import validate_assignment


class ReallocationEngine:
    """
    Advanced reallocation engine that considers:
    - Operator certifications and skill levels
    - Machine compatibility and priority
    - Current workload and fatigue
    - Shift constraints and business rules
    - Production targets and efficiency
    """
    
    def __init__(self):
        pass
    
    def find_best_reallocation(self, operator_id, shift_id, broken_machine_id=None, max_results=5):
        """
        Find the best reallocation options for an operator.
        Uses a scoring algorithm considering multiple factors.
        """
        operator = User.query.filter_by(id=operator_id, role=UserRole.OPERATOR).first()
        if not operator:
            return []
        
        shift = Shift.query.get(shift_id)
        if not shift:
            return []
        
        # Get operator's valid certifications with levels
        operator_certs = OperatorCertification.query.filter(
            OperatorCertification.user_id == operator_id,
            OperatorCertification.status == CertificationStatus.ACTIVE
        ).all()
        
        cert_map = {}
        for oc in operator_certs:
            if oc.is_valid():
                cert_map[oc.certification_id] = oc.certification.level
        
        # Get assigned machines in this shift
        assigned_machine_ids = db.session.query(ShiftAssignment.machine_id).filter(
            ShiftAssignment.shift_id == shift_id,
            ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED])
        ).subquery()
        
        # Get all available machines
        query = Machine.query.filter(
            Machine.is_active == True,
            Machine.status.in_([MachineStatus.ACTIVE, MachineStatus.IDLE]),
            ~Machine.id.in_(assigned_machine_ids)
        )
        
        if broken_machine_id:
            query = query.filter(Machine.id != broken_machine_id)
        
        available_machines = query.all()
        
        scored_machines = []
        
        for machine in available_machines:
            score = self._calculate_reallocation_score(
                machine, operator, cert_map, shift, broken_machine_id
            )
            
            if score > 0:
                scored_machines.append({
                    'machine': machine,
                    'score': score,
                    'details': self._get_score_details(machine, operator, cert_map, shift, broken_machine_id)
                })
        
        # Sort by score descending
        scored_machines.sort(key=lambda x: x['score'], reverse=True)
        
        # Format results
        results = []
        for item in scored_machines[:max_results]:
            m = item['machine']
            results.append({
                'machine_id': m.id,
                'machine_code': m.machine_code,
                'machine_name': m.name,
                'machine_type': m.machine_type.name if m.machine_type else 'Unknown',
                'floor_zone': m.floor_zone,
                'location_x': m.location_x,
                'location_y': m.location_y,
                'current_status': m.status.value,
                'match_score': item['score'],
                'score_details': item['details'],
                'required_certifications': [
                    {'id': c.id, 'name': c.name, 'code': c.code, 'level': c.level}
                    for c in m.machine_type.required_certifications or []
                ] if m.machine_type and m.machine_type.required_certifications else []
            })
        
        return results
    
    def _calculate_reallocation_score(self, machine, operator, cert_map, shift, broken_machine_id):
        """Calculate a composite score for machine-operator fit"""
        score = 0
        
        # 1. Certification match (base score)
        required_certs = set(machine.machine_type.required_certifications or []) if machine.machine_type else set()
        if required_certs:
            matched = required_certs & set(cert_map.keys())
            if len(matched) == len(required_certs):
                score += 40  # Perfect match
            elif len(matched) > 0:
                score += 20 * (len(matched) / len(required_certs))  # Partial match
            else:
                return 0  # No certification match
        else:
            score += 20  # No certs required
        
        # 2. Machine status preference
        if machine.status == MachineStatus.IDLE:
            score += 20  # Prefer idle machines
        elif machine.status == MachineStatus.ACTIVE:
            score += 10  # Active is ok
        
        # 3. Same machine type as broken machine (continuity)
        if broken_machine_id:
            broken_machine = Machine.query.get(broken_machine_id)
            if broken_machine and broken_machine.machine_type_id == machine.machine_type_id:
                score += 15
        
        # 4. Floor zone proximity (if operator was on nearby machine)
        # This would need operator's previous machine location
        
        # 5. Operator workload balance
        workload = self._get_operator_workload_today(operator.id, shift_id)
        if workload['hours'] < shift.duration_hours * 0.8:
            score += 10  # Not overworked
        
        # 6. Machine priority/criticality
        if machine.capacity_max and machine.capacity_max > 1000:
            score += 5  # High capacity machines get slight priority
        
        # 7. Maintenance status
        if machine.last_maintenance:
            hours_since = (datetime.utcnow() - machine.last_maintenance).total_seconds() / 3600
            if hours_since < machine.maintenance_interval_hours * 0.5:
                score += 5  # Recently maintained
        
        return min(score, 100)
    
    def _get_score_details(self, machine, operator, cert_map, shift, broken_machine_id):
        """Get detailed breakdown of score components"""
        details = {}
        
        required_certs = set(machine.machine_type.required_certifications or []) if machine.machine_type else set()
        matched = required_certs & set(cert_map.keys())
        details['certification_match'] = {
            'required': len(required_certs),
            'matched': len(matched),
            'percentage': round(len(matched) / len(required_certs) * 100, 1) if required_certs else 100
        }
        
        details['machine_status'] = machine.status.value
        details['same_type_as_broken'] = False
        if broken_machine_id:
            broken_machine = Machine.query.get(broken_machine_id)
            details['same_type_as_broken'] = (
                broken_machine and broken_machine.machine_type_id == machine.machine_type_id
            )
        
        workload = self._get_operator_workload_today(operator.id, shift_id)
        details['workload_hours_today'] = workload['hours']
        details['shift_duration'] = shift.duration_hours
        
        return details
    
    def _get_operator_workload_today(self, operator_id, shift_id):
        """Get operator's assigned hours for the day of the shift"""
        shift = Shift.query.get(shift_id)
        if not shift:
            return {'hours': 0}
        
        # Get date of shift (assume today for now)
        shift_date = date.today()
        
        assignments = ShiftAssignment.query.filter(
            ShiftAssignment.operator_id == operator_id,
            ShiftAssignment.assigned_at >= datetime.combine(shift_date, time.min),
            ShiftAssignment.assigned_at < datetime.combine(shift_date + timedelta(days=1), time.min),
            ShiftAssignment.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.STARTED, AssignmentStatus.COMPLETED])
        ).all()
        
        total_hours = sum(a.shift.duration_hours for a in assignments if a.shift)
        return {'hours': total_hours}
    
    def find_cascade_reallocation(self, shift_id, max_depth=3):
        """
        Find cascade reallocation options when multiple machines go down.
        Returns a plan for reassigning multiple operators.
        """
        # Find all fault/offline machines with active assignments
        fault_machines = Machine.query.filter(
            Machine.status.in_([MachineStatus.FAULT, MachineStatus.OFFLINE]),
            Machine.is_active == True
        ).all()
        
        cascade_plan = []
        
        for machine in fault_machines:
            assignment = ShiftAssignment.query.filter_by(
                shift_id=shift_id,
                machine_id=machine.id,
                status=AssignmentStatus.STARTED
            ).first()
            
            if assignment:
                recommendations = self.find_best_reallocation(
                    assignment.operator_id, shift_id, machine.id
                )
                
                cascade_plan.append({
                    'broken_machine': {
                        'id': machine.id,
                        'code': machine.machine_code,
                        'name': machine.name
                    },
                    'displaced_operator': {
                        'id': assignment.operator_id,
                        'name': assignment.operator.name
                    },
                    'recommendations': recommendations
                })
        
        return cascade_plan
    
    def optimize_shift_assignments(self, shift_id):
        """
        Optimize all assignments for a shift using constraint satisfaction.
        Returns optimized assignment plan.
        """
        shift = Shift.query.get(shift_id)
        if not shift:
            return None
        
        # Get all active operators
        operators = User.query.filter_by(role=UserRole.OPERATOR, is_active=True).all()
        
        # Get all available machines
        machines = Machine.query.filter_by(is_active=True).filter(
            Machine.status.in_([MachineStatus.ACTIVE, MachineStatus.IDLE])
        ).all()
        
        # Build bipartite graph: operators -> compatible machines
        compatibility = {}
        for op in operators:
            op_certs = OperatorCertification.query.filter(
                OperatorCertification.user_id == op.id,
                OperatorCertification.status == CertificationStatus.ACTIVE
            ).all()
            valid_certs = set(c.certification_id for c in op_certs if c.is_valid())
            
            compatible = []
            for m in machines:
                required = set(m.machine_type.required_certifications or []) if m.machine_type else set()
                if required.issubset(valid_certs):
                    compatible.append(m.id)
            
            if compatible:
                compatibility[op.id] = compatible
        
        # Greedy assignment: sort operators by fewest options first
        sorted_ops = sorted(compatibility.keys(), key=lambda o: len(compatibility[o]))
        
        assigned_machines = set()
        assignments = []
        
        for op_id in sorted_ops:
            for m_id in compatibility[op_id]:
                if m_id not in assigned_machines:
                    # Check business rules
                    is_valid, _ = validate_assignment(shift_id, m_id, op_id)
                    if is_valid:
                        assigned_machines.add(m_id)
                        assignments.append({
                            'operator_id': op_id,
                            'machine_id': m_id
                        })
                        break
        
        return {
            'shift_id': shift_id,
            'assignments': assignments,
            'unassigned_operators': [o for o in operators if o.id not in [a['operator_id'] for a in assignments]],
            'unassigned_machines': [m for m in machines if m.id not in assigned_machines]
        }


# Global instance
reallocation_engine = ReallocationEngine()


def find_reallocation_options(operator_id, shift_id, broken_machine_id=None):
    """Convenience function for API"""
    return reallocation_engine.find_best_reallocation(operator_id, shift_id, broken_machine_id)