# TexWorkforce Optimizer - API Specification

**Version:** 1.0.0  
**Base URL:** `http://localhost:5000/api`  
**Authentication:** JWT Bearer Token (HTTP-only cookies)

---

## Authentication

All API endpoints (except `/auth/login`) require a valid JWT token in the Authorization header or HTTP-only cookie.

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "employee_id": "OPR001",
  "password": "Operator@123"
}
```

**Response:**
```json
{
  "user": {
    "id": 1,
    "employee_id": "OPR001",
    "name": "John Doe",
    "email": "john.doe@texworkforce.com",
    "role": "operator",
    "department_id": 1,
    "shift_pattern": "morning",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
}
```

### Logout
```http
POST /auth/logout
```

### Refresh Token
```http
POST /auth/refresh
```

### Get Current User
```http
GET /auth/me
```

---

## Machines

### List Machines
```http
GET /machines?page=1&per_page=20&status=active&type_id=1&zone=A&search=RSF
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `per_page` (int): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (active, idle, maintenance, fault, offline, disconnected)
- `type_id` (int): Filter by machine type ID
- `department_id` (int): Filter by department ID
- `zone` (string): Filter by floor zone
- `search` (string): Search in machine code or name
- `include_inactive` (bool): Include inactive machines (default: false)

### Get Machine Details
```http
GET /machines/{id}?include_telemetry=true
```

### Create Machine (Admin)
```http
POST /machines
Content-Type: application/json

{
  "machine_code": "RSF-04",
  "name": "Ring Spinning Frame 4",
  "machine_type_id": 1,
  "department_id": 1,
  "location_x": 400,
  "location_y": 100,
  "floor_zone": "A",
  "capacity_max": 500,
  "maintenance_interval_hours": 8
}
```

### Update Machine (Admin)
```http
PUT /machines/{id}
Content-Type: application/json

{
  "name": "Updated Name",
  "capacity_max": 550,
  "floor_zone": "B"
}
```

### Update Machine Status (System/Supervisor)
```http
PUT /machines/{id}/status
Content-Type: application/json

{
  "status": "fault",
  "rpm": 0,
  "temperature": 45.5,
  "vibration": 5.2,
  "error_code": "YARN_BREAK",
  "reason": "Yarn breakage detected"
}
```

### Get Machine Telemetry
```http
GET /machines/{id}/telemetry?hours=24&page=1&per_page=50
```

### Get Machine Downtime History
```http
GET /machines/{id}/downtime?page=1&per_page=20
```

### List Machine Types
```http
GET /machines/types
```

### Create Machine Type (Admin)
```http
POST /machines/types
Content-Type: application/json

{
  "name": "New Machine Type",
  "code": "NMT",
  "description": "Description",
  "required_certifications": [1, 2],
  "default_capacity": 100,
  "maintenance_interval_hours": 8
}
```

### Get Floor Map Data
```http
GET /machines/floor-map
```

### Get Machine Statistics
```http
GET /machines/stats/summary
```

---

## Operators

### List Operators
```http
GET /operators?page=1&per_page=20&search=john&certification_id=1&available=true
```

**Query Parameters:**
- `page`, `per_page`: Pagination
- `search`: Search in name or employee ID
- `certification_id`: Filter by certification
- `department_id`: Filter by department
- `shift_pattern`: Filter by shift pattern
- `available`: Only show operators not assigned in current shift

### Get Operator Details
```http
GET /operators/{id}
```

### Get Operator Schedule
```http
GET /operators/{id}/schedule?start_date=2024-01-01&end_date=2024-01-31
```

### Add/Update Certification (Admin)
```http
POST /operators/{id}/certifications
Content-Type: application/json

{
  "certification_id": 1,
  "obtained_date": "2024-01-15",
  "expiry_date": "2025-01-15",
  "notes": "Initial certification"
}
```

### Update Certification (Admin)
```http
PUT /operators/{id}/certifications/{cert_id}
Content-Type: application/json

{
  "status": "active",
  "expiry_date": "2025-06-15"
}
```

### Revoke Certification (Admin)
```http
DELETE /operators/{id}/certifications/{cert_id}
```

### List Certification Types
```http
GET /operators/certifications
```

### Create Certification Type (Admin)
```http
POST /operators/certifications
Content-Type: application/json

{
  "name": "New Certification",
  "code": "NCT",
  "level": 1,
  "description": "Description",
  "validity_months": 12
}
```

### Get Available Operators for Machine
```http
GET /operators/available-for-machine/{machine_id}?shift_id=1
```

---

## Shifts

### List Shifts
```http
GET /shifts
```

### Create Shift (Admin)
```http
POST /shifts
Content-Type: application/json

{
  "name": "Morning Shift",
  "code": "MOR",
  "start_time": "06:00",
  "end_time": "14:00",
  "rest_period_hours": 11
}
```

### Get Shift with Assignments
```http
GET /shifts/{id}
```

### Get Shift Assignments
```http
GET /shifts/{id}/assignments
```

### Create Assignment (Supervisor)
```http
POST /shifts/{shift_id}/assignments
Content-Type: application/json

{
  "machine_id": 1,
  "operator_id": 5,
  "supervisor_id": 2,
  "notes": "Assigned to morning shift"
}
```

### Update Assignment (Supervisor)
```http
PUT /shifts/assignments/{id}
Content-Type: application/json

{
  "status": "started",
  "notes": "Shift started on time"
}
```

### Delete Assignment (Supervisor)
```http
DELETE /shifts/assignments/{id}
```

### Validate Assignment
```http
POST /shifts/assignments/validate
Content-Type: application/json

{
  "shift_id": 1,
  "machine_id": 5,
  "operator_id": 3
}
```

### Get Unassigned Machines for Shift
```http
GET /shifts/{shift_id}/unassigned-machines
```

### Get Available Operators for Shift
```http
GET /shifts/{shift_id}/available-operators?machine_id=1
```

### Get Today's Shifts
```http
GET /shifts/today
```

### Start Shift (Supervisor)
```http
POST /shifts/{shift_id}/start
```

### End Shift (Supervisor)
```http
POST /shifts/{shift_id}/end
```

---

## Reallocation

### Get Reallocation Recommendations
```http
POST /reallocation/recommend
Content-Type: application/json

{
  "operator_id": 5,
  "shift_id": 1,
  "machine_id": 3
}
```

**Response:**
```json
{
  "operator_id": 5,
  "shift_id": 1,
  "recommendations": [
    {
      "machine_id": 7,
      "machine_code": "AJL-03",
      "machine_name": "Air Jet Loom 3",
      "machine_type": "Air Jet Loom",
      "floor_zone": "B",
      "current_status": "idle",
      "match_score": 95,
      "score_details": {
        "certification_match": {"required": 2, "matched": 2, "percentage": 100},
        "same_type_as_broken": true,
        "workload_hours_today": 0
      }
    }
  ]
}
```

### Approve Reallocation
```http
POST /reallocation/approve
Content-Type: application/json

{
  "operator_id": 5,
  "shift_id": 1,
  "new_machine_id": 7,
  "reason": "Machine fault on JQL-01"
}
```

### Get Reallocation History
```http
GET /reallocation/history?page=1&per_page=20&operator_id=5&days=30
```

### Auto-Suggest Reallocations for Shift
```http
POST /reallocation/auto-suggest
Content-Type: application/json

{
  "shift_id": 1
}
```

---

## Reports

### Get Daily Report
```http
GET /reports/daily?date=2024-01-15&shift_id=1
```

### Get Shift Report
```http
GET /reports/shift/{shift_id}?date=2024-01-15
```

### Get Machine Report
```http
GET /reports/machine/{machine_id}?days=30
```

### Get Operator Report
```http
GET /reports/operator/{operator_id}?days=30
```

### Export Report
```http
POST /reports/export
Content-Type: application/json

{
  "type": "shift",
  "format": "pdf",
  "params": {
    "shift_id": 1,
    "date": "2024-01-15"
  }
}
```

**Formats:** `pdf`, `excel`  
**Types:** `daily`, `shift`, `machine`, `operator`

### Get Machine OEE
```http
GET /reports/oee/{machine_id}?days=30
```

### Get Production Summary
```http
GET /reports/summary?days=7&shift_id=1
```

---

## Alerts

### List Alerts
```http
GET /alerts?page=1&per_page=20&type=machine_fault&severity=critical&is_read=false&days=30
```

### Get Unread Alert Count
```http
GET /alerts/unread-count
```

### Acknowledge Alert
```http
PUT /alerts/{id}/acknowledge
```

### Acknowledge All Alerts (Supervisor)
```http
PUT /alerts/acknowledge-all
Content-Type: application/json

{
  "type": "machine_fault",
  "machine_id": 1
}
```

### List Alert Types
```http
GET /alerts/types
```

---

## WebSocket Events

### Connection
```javascript
const socket = io('http://localhost:5000', {
  auth: { token: 'your-jwt-token' }
});
```

### Client Events
- `join_shift` - Join shift room: `{ shift_id: 1 }`
- `leave_shift` - Leave shift room: `{ shift_id: 1 }`
- `subscribe_machine` - Subscribe to machine: `{ machine_id: 1 }`
- `unsubscribe_machine` - Unsubscribe: `{ machine_id: 1 }`
- `ping` - Health check

### Server Events
- `connected` - Connection confirmed
- `machine_status_update` - Machine status changed
- `machine_telemetry` - New telemetry data
- `assignment_created` - New assignment created
- `assignment_updated` - Assignment updated
- `assignment_deleted` - Assignment deleted
- `shift_started` - Shift started
- `shift_ended` - Shift ended
- `new_alert` - New alert created
- `alert_acknowledged` - Alert acknowledged
- `reallocation_approved` - Reallocation approved

---

## Error Responses

### 400 Bad Request
```json
{
  "error": "Validation error message"
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 422 Unprocessable Entity
```json
{
  "error": "Business rule violation",
  "details": "Operator missing required certification"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Rate Limiting

- Login attempts: 5 per minute per IP
- API requests: 100 per minute per user
- WebSocket connections: 1 per user

---

## Pagination Response Format

```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```