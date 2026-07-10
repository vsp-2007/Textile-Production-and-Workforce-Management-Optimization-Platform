import re
from datetime import datetime, date


def validate_password_strength(password, employee_id, name):
    """
    Validate password meets requirements:
    - 8+ characters
    - At least one uppercase letter
    - At least one digit
    - At least one special character
    - Must not contain employee's name or ID
    """
    if not password:
        return False, 'Password is required'
    
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long'
    
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter'
    
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit'
    
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':",./<>?\\|`~]', password):
        return False, 'Password must contain at least one special character'
    
    if employee_id and employee_id.lower() in password.lower():
        return False, 'Password must not contain employee ID'
    
    if name:
        name_parts = name.lower().split()
        for part in name_parts:
            if len(part) >= 3 and part in password.lower():
                return False, 'Password must not contain employee name'
    
    return True, 'Password is valid'


def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_employee_id(employee_id):
    """Validate employee ID format (alphanumeric, 3-50 chars)"""
    if not employee_id:
        return False
    pattern = r'^[A-Za-z0-9]{3,50}$'
    return bool(re.match(pattern, employee_id))


def generate_session_token():
    """Generate secure session token"""
    import secrets
    return secrets.token_urlsafe(32)


def validate_shift_timing(start_time, end_time, max_hours=12):
    """Validate shift timing doesn't exceed max hours"""
    if isinstance(start_time, str):
        start_time = datetime.strptime(start_time, '%H:%M').time()
    if isinstance(end_time, str):
        end_time = datetime.strptime(end_time, '%H:%M').time()
    
    start_dt = datetime.combine(date.today(), start_time)
    end_dt = datetime.combine(date.today(), end_time)
    
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    
    duration = (end_dt - start_dt).total_seconds() / 3600
    return duration <= max_hours, duration


def validate_rest_period(last_shift_end, next_shift_start, min_hours=11):
    """Validate minimum rest period between shifts"""
    if isinstance(last_shift_end, str):
        last_shift_end = datetime.fromisoformat(last_shift_end)
    if isinstance(next_shift_start, str):
        next_shift_start = datetime.fromisoformat(next_shift_start)
    
    rest_hours = (next_shift_start - last_shift_end).total_seconds() / 3600
    return rest_hours >= min_hours, rest_hours


def sanitize_input(text, max_length=500):
    """Sanitize user input"""
    if not text:
        return ''
    # Remove potential XSS vectors
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    return text[:max_length].strip()


def validate_machine_code(code):
    """Validate machine code format"""
    if not code:
        return False
    pattern = r'^[A-Z0-9\-]{3,50}$'
    return bool(re.match(pattern, code.upper()))


def validate_certification_code(code):
    """Validate certification code format"""
    if not code:
        return False
    pattern = r'^[A-Z0-9]{2,20}$'
    return bool(re.match(pattern, code.upper()))