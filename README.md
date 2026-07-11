# TexWorkforce Optimizer

> **Manufacturing Execution System (MES) & Workforce Management Platform for Textile Industry**

[![Build Status](https://github.com/vsp-2007/Textile-Production-and-Workforce-Management-Optimization-Platform/workflows/CI/badge.svg)](https://github.com/vsp-2007/Textile-Production-and-Workforce-Management-Optimization-Platform/actions)
[![Coverage](https://img.shields.io/badge/coverage-80%25-brightgreen)](https://github.com/vsp-2007/Textile-Production-and-Workforce-Management-Optimization-Platform)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://python.org)
[![React](https://img.shields.io/badge/react-18+-blue)](https://reactjs.org)

## 📋 Overview

**TexWorkforce Optimizer** is an enterprise-grade Manufacturing Execution System (MES) and Workforce Management (WFM) platform designed specifically for the textile manufacturing industry. It bridges the critical gap between machine performance data and workforce allocation, enabling real-time optimization of production operations.

### Problem Statement
Modern textile mills suffer from disconnected workflows where machine performance data and workforce allocation are managed in distinct, manual silos. This leads to:
- Production delays and inefficient resource utilization
- Communication gaps between departments
- Increased operational costs and reduced productivity
- Difficulty monitoring production progress and identifying bottlenecks

### Solution
TexWorkforce Optimizer provides a unified digital dashboard that dynamically pairs active machine demands with qualified human capital to minimize downtime and maximize yard-yield.

---

## ✨ Key Features

### 🏭 Real-Time Machine Monitoring
- **Live telemetry** from IoT-enabled machines (spinning, weaving, dyeing, finishing)
- **Status tracking**: Active, Idle, Maintenance, Fault, Offline, Disconnected
- **Interactive floor map** with color-coded machine visualization
- **Sub-second dashboard updates** (< 1.2s latency)

### 👥 Skill-Based Workforce Scheduling
- **Certification management** (Jacquard Weaving L3, Blowroom Carding L1, etc.)
- **Automatic validation** of operator qualifications before assignment
- **Double-booking prevention** with shift conflict detection
- **Rest period enforcement** (11-hour minimum between shifts)

### 🔄 Automated Reallocation Engine
- **Intelligent recommendations** when machines break down
- **Skill matching** algorithm finds best alternative assignments
- **Supervisor approval workflow** with real-time notifications
- **Cascade reallocation** for multiple simultaneous faults

### 📊 Comprehensive Reporting
- **Daily production efficiency** reports
- **Shift utilization** analytics
- **Machine OEE** (Overall Equipment Effectiveness) calculations
- **Operator productivity** tracking
- **Export to PDF/Excel** with thermal printer support

### 🔔 Real-Time Alerts
- Machine fault notifications (SMS/Email)
- Idle machine warnings
- Maintenance due reminders
- Certification expiry alerts
- Shift violation warnings

### 🎨 Multi-Role Interface
| Role | Interface | Key Features |
|------|-----------|--------------|
| **Plant Admin** | Configuration Suite | Machine registration, user management, analytics |
| **Shift Supervisor** | Touchscreen Dashboard | Floor map, drag-drop scheduling, alerts, reallocation |
| **Machine Operator** | High-Contrast Terminal | Schedule view, clock-in, delay reporting, maintenance requests |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TexWorkforce Optimizer                       │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    HTTPS/TLS    ┌─────────────────────────┐   │
│  │   Browser   │ ◄─────────────► │   Flask + SocketIO      │   │
│  │  (React)    │    WebSocket    │   (Python 3.11+)        │   │
│  └─────────────┘                 └───────────┬─────────────┘   │
│                                              │                 │
│                                              ▼                 │
│                                    ┌───────────────────────┐   │
│                                    │    MySQL 8.0          │   │
│                                    │    (ACID Transactions)│   │
│                                    └───────────┬───────────┘   │
│                                                │               │
│                                                ▼               │
│                              ┌─────────────────────────────┐   │
│                              │      MQTT Broker            │   │
│                              │    (Eclipse Mosquitto)      │   │
│                              └──────────────┬──────────────┘   │
│                                             │                  │
│                                             ▼                  │
│                              ┌─────────────────────────────┐   │
│                              │   Floor Controllers         │   │
│                              │   (Weaving/Spinning/Dyeing) │   │
│                              └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| **Frontend** | React + Vite + Bootstrap 5 | 18.2 / 5.3 |
| **Backend** | Flask + SocketIO + SQLAlchemy | 3.0 / 5.3 / 2.0 |
| **Database** | MySQL | 8.0 |
| **Messaging** | MQTT (paho-mqtt) + WebSocket | 5.0 / 1.6 |
| **Async Tasks** | Celery + Redis | 5.3 / 7.0 |
| **Auth** | JWT (HTTP-only cookies) | - |
| **Charts** | Chart.js + Recharts | 4.4 / 2.10 |
| **Export** | ReportLab + OpenPyXL | 4.1 / 3.1 |
| **Testing** | Pytest + Selenium + Vitest | 8.1 / 4.0 / 1.3 |

---

## 🚀 Quick Start

### Prerequisites
- Docker 24+ and Docker Compose 2.20+
- 4GB+ RAM available
- Ports 3306, 1883, 5000, 5173, 6379 available

### 1. Clone & Configure
```bash
git clone https://github.com/vsp-2007/Textile-Production-and-Workforce-Management-Optimization-Platform.git
cd Textile-Production-and-Workforce-Management-Optimization-Platform

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your settings
```

### 2. Start Development Environment
```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend flask db upgrade
docker-compose exec backend flask seed-db
```

### 3. Access Applications
| Service | URL |
|---------|-----|
| **Frontend** | http://localhost:5173 |
| **Backend API** | http://localhost:5000/api |
| **API Docs** | See `docs/API_SPEC.md` |

### 4. Demo Credentials
| Role | Employee ID | Password |
|------|-------------|----------|
| **Admin** | `ADMIN001` | `Admin@123` |
| **Supervisor** | `SUPV001` | `Supervisor@123` |
| **Operator** | `OPR001` | `Operator@123` |

---

## 📁 Project Structure

```
TexWorkforce-Optimizer/
├── 📄 PROJECT_PLAN.md          # Comprehensive project plan
├── 📄 docker-compose.yml       # Development environment
├── 📄 sonar-project.properties # SonarCloud config
├── 📄 README.md                # This file
│
├── 📂 backend/                 # Flask API Server
│   ├── 📂 app/
│   │   ├── 📂 api/            # REST endpoints (auth, machines, operators, shifts, etc.)
│   │   ├── 📂 models/         # SQLAlchemy models
│   │   ├── 📂 services/       # Business logic (MQTT, scheduler, reallocation, reports)
│   │   ├── 📂 websocket/      # Real-time event handlers
│   │   ├── 📂 utils/          # Security, validators
│   │   └── 📂 cli.py          # Database commands
│   ├── 📄 requirements.txt    # Python dependencies
│   ├── 📄 run.py              # Entry point
│   └── 📄 Dockerfile
│
├── 📂 frontend/               # React + Vite Application
│   ├── 📂 src/
│   │   ├── 📂 components/     # Reusable UI components
│   │   ├── 📂 pages/          # Page components (Login, Dashboards, etc.)
│   │   ├── 📂 services/       # API client, WebSocket
│   │   ├── 📂 hooks/          # Custom React hooks
│   │   ├── 📂 store/          # Zustand state management
│   │   └── 📂 styles/         # CSS modules
│   ├── 📄 package.json
│   └── 📄 Dockerfile
│
├── 📂 database/
│   ├── 📄 schema.sql          # Complete MySQL schema
│   └── 📄 seed_data.sql       # Initial data
│
├── 📂 iot-simulator/          # MQTT Machine Simulator
│   ├── 📄 simulator.py        # Generates realistic telemetry
│   └── 📄 Dockerfile
│
├── 📂 mosquitto/              # MQTT Broker Config
│   └── 📂 config/mosquitto.conf
│
├── 📂 docs/
│   ├── 📄 API_SPEC.md         # Complete API documentation
│   ├── 📄 DEPLOYMENT.md       # Production deployment guide
│   ├── 📄 SRS.md              # Software Requirements Specification
│   └── 📄 SOP.md              # Standard Operating Procedure
│
└── 📂 .github/workflows/      # CI/CD pipelines
    ├── 📄 ci.yml              # Build, test, lint
    └── 📄 sonarqube.yml       # Code quality analysis
```

---

## 🔧 Development

### Backend Commands
```bash
cd backend
source venv/bin/activate

# Run development server
python run.py

# Database commands
flask db migrate -m "description"
flask db upgrade
flask seed-db
flask create-admin

# Testing
pytest                    # Unit tests
pytest --cov=app         # With coverage
```

### Frontend Commands
```bash
cd frontend

# Development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run tests
npm run test
npm run test:ui
```

### Running IoT Simulator
```bash
cd iot-simulator
pip install -r requirements.txt
python simulator.py

# Or with Docker
docker-compose --profile testing up -d iot-simulator
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [`PROJECT_PLAN.md`](PROJECT_PLAN.md) | Complete project plan with phases, team assignments, risks |
| [`docs/API_SPEC.md`](docs/API_SPEC.md) | Full REST API specification with examples |
| [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) | Production deployment guide |
| [`docs/SRS.md`](docs/SRS.md) | Software Requirements Specification (IEEE 830) |
| [`docs/SOP.md`](docs/SOP.md) | Standard Operating Procedure |
| [`database/schema.sql`](database/schema.sql) | Database schema (ERD) |
| [`database/seed_data.sql`](database/seed_data.sql) | Seed data for development |

---

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v --cov=app --cov-report=html
```

### Frontend Tests
```bash
cd frontend
npm run test
npm run test:coverage
```

### E2E Tests
```bash
# Requires running application
cd frontend
npm run test:e2e
```

### Code Quality
```bash
# Backend
cd backend
black .
isort .
flake8 .
mypy .

# Frontend
cd frontend
npm run lint
```

---

## 🚢 Deployment

### Production Checklist
- [ ] Change all default passwords
- [ ] Generate strong JWT secrets (64+ chars)
- [ ] Configure HTTPS/TLS certificates
- [ ] Set `JWT_COOKIE_SECURE=True`
- [ ] Configure MySQL SSL connections
- [ ] Set up MQTT authentication
- [ ] Configure SMTP/SMS for alerts
- [ ] Set up automated database backups
- [ ] Configure monitoring (Prometheus/Grafana)
- [ ] Enable SonarCloud quality gates

### Docker Production Deploy
```bash
# Build production images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale backend
docker-compose up -d --scale backend=3
```

### Manual Deployment
See [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) for detailed instructions.

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'feat: add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

### Commit Convention
```
feat: new feature
fix: bug fix
docs: documentation
style: formatting
refactor: code restructuring
test: adding tests
chore: maintenance
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---


