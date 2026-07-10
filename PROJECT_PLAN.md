# TexWorkforce Optimizer - Project Plan

> **Project:** Textile Production and Workforce Management Optimization Platform  
> **Course:** U23IT481 - Software Engineering Laboratory  
> **Product Name:** TexWorkforce Optimizer  
> **Repository:** `C:\Users\visnu\Documents\Textile Production and Workforce Management Optimization Platform`  
> **Generated:** 2026-07-08  

---

## 1. Executive Summary

**TexWorkforce Optimizer** is an enterprise-grade Manufacturing Execution System (MES) and Workforce Management (WFM) platform designed for the textile manufacturing industry. It addresses the critical gap of disconnected workflows where machine performance data and workforce allocation are managed in distinct, manual silos.

### Core Problem Statement
Modern textile mills suffer from:
- Manual record keeping, spreadsheets, and disconnected management systems
- Production delays, inefficient resource utilization, communication gaps
- Difficulty monitoring production progress, tracking machine performance, assigning workers effectively
- Inability to identify bottlenecks in manufacturing process

### Solution Objectives (from SOP)
1. **Improve production planning, monitoring, and tracking**
2. **Enhance workforce allocation and workplace efficiency**
3. **Reduce production delays and operational bottlenecks**
4. **Improve communication between management and employees**
5. **Support better decision-making through centralized information management**
6. **Increase productivity while minimizing resource wastage**

### Expected Benefits
- Better visibility of production activities
- Efficient utilization of manpower and machinery
- Reduced downtime and operational costs
- Improved coordination among departments
- Higher productivity and customer satisfaction

---

## 2. Technical Architecture

### 2.1 Technology Stack (Per SOP Requirements)

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend UI** | HTML5, CSS3, JavaScript (Bootstrap framework) | Latest |
| **Backend Logic** | Python (Flask or Django) | Python 3.10+ |
| **Database** | MySQL | 8.0 |
| **OS** | Windows / Linux | - |
| **IDE** | VS Code / PyCharm / Any | - |

### 2.2 System Architecture (Per SRS)

```
┌─────────────────────────────────────────────────────────────┐
│                    TexWorkforce Optimizer                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    HTTPS    ┌─────────────────────────┐   │
│  │ User/Browser│ ◄─────────► │ Web Server / Application │   │
│  │  Dashboard  │             │     (Python/Flask)      │   │
│  └─────────────┘             └───────────┬─────────────┘   │
│                                          │                 │
│                                          ▼                 │
│                              ┌───────────────────────┐     │
│                              │   Relational DB       │     │
│                              │   (MySQL 8.0)         │     │
│                              └───────────┬───────────┘     │
│                                          │                 │
│                                          ▼                 │
│              ┌──────────────────┐  ┌─────────────────┐    │
│              │ Floor Controllers│◄─│ IoT Gateway /   │    │
│              │ (Weaving/Spin)   │  │ API Engine      │    │
│              └──────────────────┘  │ (MQTT/TCP)      │    │
│                                     └─────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Communication Protocols
- **API:** Secure HTTPS using TLS 1.3
- **IoT/Machine Telemetry:** MQTT (Eclipse Mosquitto broker)
- **Real-time Updates:** WebSocket / Server-Sent Events
- **Alerts:** SMTP/SMS Gateways

---

## 3. User Roles & Personas

| Role | Description | Key Interfaces |
|------|-------------|----------------|
| **Plant Administrator** | High-level factory managers configuring global settings, registering machinery, managing supervisors, adjusting yield targets | Extensive configuration suite, long-term analytics |
| **Shift Supervisor** | Active floor managers managing daily operations, monitoring alerts, assigning shifts, handling reallocations, running reports | Visual, fast-loading, touchscreen-friendly dashboard |
| **Machine Operator** | Frontline workforce using terminal interfaces at machine hubs | Simple, high-contrast, large-font screens |

---

## 4. Core Functional Features (Per SRS)

### 4.1 Feature 1: Real-Time Machine Status Tracking (High Priority)
- **States:** Active, Idle (No Operator), Maintenance Needed, Offline (Fault)
- **Flow:** Sensor → IoT Gateway (MQTT) → Server → MySQL → Dashboard (WebSocket)
- **Latency:** < 1.2s dashboard update
- **Error Handling:** Invalid state logging, connection loss detection (> threshold → "Disconnected")

### 4.2 Feature 2: Skill-Based Workforce Scheduling (High Priority)
- **Certifications:** Jacquard Weaving L3, Blowroom Carding L1, etc.
- **Validation:** Type + Expiration date check
- **Constraints:** No double-booking, certification enforcement
- **Latency:** < 0.2s employee record search

### 4.3 Feature 3: Automated Reallocation Engine (Medium Priority)
- **Trigger:** Machine breakdown → Operator idle
- **Algorithm:** Match idle operator skills → Vacant compatible machines
- **Output:** Recommendation card on Supervisor dashboard
- **Latency:** < 1.5s reallocation calculation

### 4.4 Feature 4: Automated Shift Reporting
- **Reports:** Daily production efficiency, shift utilization, waste reports
- **Output:** Downloadable reports, thermal printer support

---

## 5. Non-Functional Requirements (Per SRS)

### 5.1 Performance
| Metric | Target |
|--------|--------|
| Machine Capacity | Up to 500+ distinct machines |
| Employee Capacity | Up to 1000+ employees |
| Concurrent Supervisor Sessions | Up to 50 |
| Dashboard Latency | < 1.2s |
| Query Response | < 0.2s |
| Reallocation Engine | < 1.5s |

### 5.2 Reliability & Availability
- **Uptime:** 99.5% (excluding scheduled maintenance)
- **Transactions:** MySQL ACID for all schedule writes, breakdowns, lot changes
- **Backups:** Automated daily at 11:59 PM
- **Emergency Mode:** Standalone local MySQL cache if BMS/HR connection lost

### 5.3 Security
- **Password:** 8+ chars, uppercase, digit, special char, no name/ID
- **Auth:** JWT in HTTP-only cookies (XSS prevention)
- **Session Timeout:** 15 minutes inactivity auto-logout
- **Concurrent Sessions:** Max 3 per User ID

### 5.4 Maintainability
- **Code File Limit:** ≤ 500 lines per file
- **SonarCloud Gate:** Duplication < 3%, Security Rating A, Tech Debt ≤ 5%

### 5.5 Business Rules
1. **Shift Length:** Max 12 hours/period
2. **Rest Period:** Min 11 hours between shifts
3. **Machine Maintenance:** Auto-trigger after 8 hours max capacity

---

## 6. Project Structure

```
TexWorkforce-Optimizer/
├── README.md
├── PROJECT_PLAN.md
├── docs/
│   ├── SRS.md
│   ├── SOP.md
│   ├── ERD.md
│   ├── DFD.md
│   ├── API_SPEC.md
│   └── DEPLOYMENT.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── machine.py
│   │   │   ├── schedule.py
│   │   │   ├── certification.py
│   │   │   ├── telemetry.py
│   │   │   └── report.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── machines.py
│   │   │   ├── operators.py
│   │   │   ├── schedules.py
│   │   │   ├── reallocation.py
│   │   │   └── reports.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── mqtt_client.py
│   │   │   ├── scheduler.py
│   │   │   ├── reallocation_engine.py
│   │   │   └── report_generator.py
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   └── validators.py
│   │   └── websocket/
│   │       ├── __init__.py
│   │       └── handlers.py
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   ├── run.py
│   └── .env.example
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── scheduler/
│   │   │   ├── machines/
│   │   │   └── operators/
│   │   ├── pages/
│   │   │   ├── Login.jsx
│   │   │   ├── AdminDashboard.jsx
│   │   │   ├── SupervisorDashboard.jsx
│   │   │   ├── OperatorTerminal.jsx
│   │   │   └── FloorMap.jsx
│   │   ├── hooks/
│   │   ├── services/
│   │   ├── store/
│   │   ├── utils/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── database/
│   ├── schema.sql
│   ├── seed_data.sql
│   └── migrations/
├── iot-simulator/
│   ├── simulator.py
│   ├── mqtt_publisher.py
│   └── machine_config.json
├── docker-compose.yml
├── Dockerfile.backend
├── Dockerfile.frontend
└── .github/
    └── workflows/
        ├── ci.yml
        └── sonarqube.yml
```

---

## 7. Database Schema Design (ERD)

### 7.1 Core Entities

```sql
-- Users & Authentication
users (id, employee_id, name, email, password_hash, role, department_id, 
       shift_pattern, is_active, created_at, updated_at)

roles (id, name, description, permissions_json)

-- Machines
machines (id, machine_code, name, type, location_x, location_y, floor_zone,
          capacity_max, status, last_maintenance, maintenance_interval_hours,
          created_at, updated_at)

machine_types (id, name, description, required_certifications_json)

-- Certifications & Skills
certifications (id, name, code, level, description, validity_months)

operator_certifications (id, user_id, certification_id, obtained_date, expiry_date, status)

-- Scheduling
shifts (id, name, start_time, end_time, duration_hours, rest_period_hours)

shift_assignments (id, shift_id, machine_id, operator_id, supervisor_id, 
                   status, assigned_at, started_at, ended_at, notes)

-- Telemetry & Monitoring
machine_telemetry (id, machine_id, timestamp, status, rpm, temperature, 
                   vibration, output_count, error_code, raw_payload_json)

machine_downtime (id, machine_id, start_time, end_time, reason, 
                  reported_by, resolved_by, duration_minutes)

-- Production & Reporting
production_logs (id, shift_assignment_id, machine_id, operator_id, 
                 start_time, end_time, target_yards, actual_yards, 
                 waste_yards, quality_grade, notes)

daily_reports (id, report_date, shift_id, total_machines, active_machines,
               total_operators, present_operators, total_yards, total_waste,
               avg_oee, downtime_minutes, generated_at)

-- Alerts & Notifications
alerts (id, alert_type, severity, machine_id, operator_id, shift_id,
        message, is_read, created_at, acknowledged_at, acknowledged_by)
```

### 7.2 Key Relationships
- User 1:N ShiftAssignments (as operator)
- User 1:N ShiftAssignments (as supervisor)
- Machine  Machine 1:N ShiftAssignments
- Machine 1:N MachineTelemetry
- Machine 1:N MachineDowntime
- User N:M Certifications (via operator_certifications)
- Shift 1:N ShiftAssignments

---

## 8. API Endpoints Specification

### 8.1 Authentication
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| POST | `/api/auth/login` | User login, returns JWT | All |
| POST | `/api/auth/logout` | Invalidate session | All |
| GET | `/api/auth/me` | Get current user profile | All |
| POST | `/api/auth/refresh` | Refresh access token | All |

### 8.2 Machines
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/machines` | List all machines with filters | Admin, Supervisor |
| GET | `/api/machines/:id` | Get machine details + telemetry | Admin, Supervisor |
| GET | `/api/machines/:id/telemetry` | Real-time telemetry stream (WS) | Admin, Supervisor |
| POST | `/api/machines` | Register new machine | Admin |
| PUT | `/api/machines/:id` | Update machine config | Admin |
| PUT | `/api/machines/:id/status` | Update machine status (IoT) | System |

### 8.3 Operators & Certifications
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/operators` | List operators with skills | Admin, Supervisor |
| GET | `/api/operators/:id` | Get operator profile + certs | Admin, Supervisor, Operator(self) |
| GET | `/api/operators/:id/schedule` | Get operator's shift schedule | Admin, Supervisor, Operator(self) |
| POST | `/api/operators` | Create operator profile | Admin |
| PUT | `/api/operators/:id/certifications` | Add/update certification | Admin |
| GET | `/api/certifications` | List all certification types | Admin, Supervisor |

### 8.4 Scheduling
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/shifts` | List shifts | All |
| GET | `/api/shifts/:id/assignments` | Get shift assignments | Admin, Supervisor |
| POST | `/api/shifts/:id/assignments` | Assign operator to machine | Supervisor |
| PUT | `/api/shifts/assignments/:id` | Update assignment | Supervisor |
| DELETE | `/api/shifts/assignments/:id` | Remove assignment | Supervisor |
| POST | `/api/shifts/assignments/validate` | Validate cert + no double-book | Supervisor |

### 8.5 Reallocation Engine
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| POST | `/api/reallocation/recommend` | Get recommendations for idle operator | Supervisor |
| POST | `/api/reallocation/approve` | Approve reallocation | Supervisor |
| GET | `/api/reallocation/history` | Reallocation history | Admin, Supervisor |

### 8.6 Reports
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/reports/daily` | Daily production report | Admin, Supervisor |
| GET | `/api/reports/shift/:id` | Shift-specific report | Admin, Supervisor |
| GET | `/api/reports/machine/:id` | Machine performance report | Admin, Supervisor |
| GET | `/api/reports/operator/:id` | Operator productivity report | Admin, Supervisor |
| POST | `/api/reports/export` | Export report (PDF/Excel) | Admin, Supervisor |

### 8.7 Alerts
| Method | Endpoint | Description | Roles |
|--------|----------|-------------|-------|
| GET | `/api/alerts` | List alerts (with filters) | Admin, Supervisor |
| PUT | `/api/alerts/:id/acknowledge` | Acknowledge alert | Supervisor |
| GET | `/api/alerts/unread-count` | Unread alert count | Supervisor |

---

## 9. Implementation Phases

### Phase 1: Foundation (Week 1-2) ✅ **IN PROGRESS**
- [x] Project plan creation
- [ ] Repository setup & Git workflow
- [ ] Database schema creation (MySQL)
- [ ] Backend project structure (Flask/FastAPI)
- [ ] Frontend project structure (Vite + React + Bootstrap)
- [ ] Docker Compose for local dev
- [ ] Basic CI/CD pipeline

### Phase 2: Core Backend (Week 2-3)
- [ ] User authentication (JWT, roles, password policy)
- [ ] Machine CRUD + status management
- [ ] Operator management + certifications
- [ ] Shift scheduling CRUD
- [ ] Validation logic (certifications, double-booking, business rules)

### Phase 3: Real-time & IoT (Week 3-4)
- [ ] MQTT client for machine telemetry
- [ ] WebSocket server for real-time dashboard updates
- [ ] IoT simulator for testing
- [ ] Machine state machine (Active/Idle/Maintenance/Fault/Offline)
- [ ] Connection loss detection & alerting

### Phase 4: Scheduling & Reallocation Engine (Week 4-5)
- [ ] Drag-and-drop scheduling UI
- [ ] Skill-based assignment validation
- [ ] Reallocation algorithm (skill matching + vacancy search)
- [ ] Recommendation UI for supervisors
- [ ] Approval workflow

### Phase 5: Reporting & Analytics (Week 5-6)
- [ ] Daily production reports
- [ ] Shift utilization reports
- [ ] Machine OEE calculations
- [ ] Operator productivity reports
- [ ] Export (PDF/Excel) + Thermal printer support

### Phase 6: Frontend Dashboards (Week 6-7)
- [ ] Login portal with role routing
- [ ] Admin dashboard (config, analytics, user mgmt)
- [ ] Supervisor dashboard (floor map, scheduling, alerts, reallocation)
- [ ] Operator terminal (schedule, clock-in, maintenance requests)
- [ ] Responsive + touchscreen + high-contrast themes

### Phase 7: Testing & Polish (Week 7-8)
- [ ] Unit tests (JUnit/pytest) - target >80% coverage
- [ ] Integration tests (API, DB)
- [ ] E2E tests (Selenium) - critical user paths
- [ ] SonarCloud integration
- [ ] Performance testing (latency benchmarks)
- [ ] Security audit (JWT, XSS, SQL injection)

### Phase 8: Documentation & Deployment (Week 8)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] ERD & DFD diagrams
- [ ] User manuals per role
- [ ] Deployment guide (Docker, systemd)
- [ ] Final presentation preparation

---

## 10. Team Assignment (Subagent Delegation)

### Subagent 1: Backend API Developer
**Focus:** Core REST API, Auth, Database Models, Business Logic
**Deliverables:**
- Flask/FastAPI project with modular structure
- SQLAlchemy models for all entities
- JWT authentication with role-based access
- CRUD APIs for machines, operators, shifts, certifications
- Validation services (business rules)
- Unit tests for all services

### Subagent 2: Real-time & IoT Engineer
**Focus:** MQTT, WebSockets, Machine Telemetry, Simulator
**Deliverables:**
- MQTT client service (Eclipse Mosquitto)
- WebSocket handler for real-time updates
- Machine state machine implementation
- IoT simulator (configurable machine behaviors)
- Connection monitoring & alerting
- Integration tests for telemetry flow

### Subagent 3: Scheduling & Reallocation Specialist
**Focus:** Shift Scheduling, Drag-and-drop UI, Reallocation Algorithm
**Deliverables:**
- Shift management API
- Assignment validation engine
- Reallocation algorithm (skill matching + optimization)
- Recommendation API
- Supervisor scheduling UI components
- Business rule enforcement (shift limits, rest periods)

### Subagent 4: Frontend Dashboard Developer
**Focus:** React Dashboards, Floor Map, Operator Terminal, Reports UI
**Deliverables:**
- Role-based routing & layouts
- Admin dashboard (config, analytics)
- Supervisor dashboard (floor map, scheduler, alerts)
- Operator terminal (simplified, high-contrast)
- Real-time charts (Chart.js / Recharts)
- Responsive + touchscreen + themes

### Subagent 5: Reporting & QA Engineer
**Focus:** Reports, Export, Testing, CI/CD, Documentation
**Deliverables:**
- Report generation service (daily, shift, machine, operator)
- PDF/Excel export (reportlab / openpyxl)
- Thermal printer integration
- Unit/E2E test suites
- SonarCloud CI pipeline
- API docs, ERD, DFD, deployment guide

---

## 11. Development Standards

### 11.1 Code Quality
- **Max file length:** 500 lines
- **Linting:** flake8 (Python), ESLint (JS)
- **Formatting:** black (Python), Prettier (JS)
- **Type hints:** Required for all Python functions
- **Docstrings:** Google style for all public functions/classes

### 11.2 Git Workflow
- **Main branch:** `main` (protected)
- **Feature branches:** `feature/<ticket>-<description>`
- **Commits:** Conventional commits (`feat:`, `fix:`, `docs:`, `refactor:`)
- **PR required** for all merges to main
- **CI checks:** Lint, type-check, tests, SonarCloud gate

### 11.3 Testing Standards
- **Unit tests:** pytest (backend), Vitest (frontend) - >80% coverage
- **Integration tests:** Testcontainers for MySQL
- **E2E tests:** Selenium/WebDriver for critical paths
- **Contract tests:** API schema validation

---

## 12. Risk Assessment & Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MQTT/WebSocket complexity | High | High | Start with simulator; use established libraries (paho-mqtt, flask-socketio) |
| Real-time performance | Medium | High | Load test early; optimize DB indexes; use Redis for caching |
| Certification logic edge cases | Medium | Medium | Comprehensive test matrix; property-based testing |
| Touchscreen UI on industrial displays | Medium | Medium | Test on target hardware early; responsive breakpoints |
| MySQL transaction deadlocks | Low | High | Consistent lock ordering; retry logic; monitoring |
| Scope creep (academic deadline) | High | High | Strict phase gates; MVP first; stretch goals documented |

---

## 13. Success Criteria (Academic Evaluation)

Per SRS Section 1.1, this project will be evaluated on:
1. **Design Quality** - ERD, DFD, Use Cases, Class Diagrams
2. **Database Construction** - Normalized MySQL schema, migrations
3. **API Endpoints** - RESTful, documented, tested
4. **Testing Frameworks** - Selenium (E2E), JUnit/pytest (unit)
5. **Code Quality Audits** - SonarCloud gate passing
6. **Functional Demo** - All 3 user roles working end-to-end
7. **Documentation** - SRS alignment, API docs, user manuals

---

## 14. Next Immediate Actions

1. **Initialize repository** with proper structure
2. **Create database schema** (MySQL + SQLAlchemy models)
3. **Set up Flask/FastAPI backend** with auth
4. **Set up Vite+React frontend** with Bootstrap
5. **Create docker-compose.yml** for MySQL, Mosquitto, backend, frontend
6. **Configure CI/CD** with GitHub Actions + SonarCloud

---

## 15. Appendix: Key References

- **SRS Document:** `docs/SRS.md` (converted from SRS_full.txt)
- **SOP Document:** `docs/SOP.md` (converted from SOP for Problem Statement.docx)
- **IEEE Std 830-1993** - SRS Standard
- **K.K. Aggarwal & Yogesh Singh** - Software Engineering
- **Pankaj Jalote** - An Integrated Approach to Software Engineering

---

*This plan is a living document. Update as implementation progresses and requirements evolve.*