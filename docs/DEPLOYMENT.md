# TexWorkforce Optimizer - Deployment Guide

## Overview

This guide covers deploying TexWorkforce Optimizer in development and production environments.

---

## Prerequisites

### System Requirements
- **OS**: Linux (Ubuntu 22.04+ recommended) or Windows with WSL2
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: Minimum 10GB free space
- **Ports**: 3306 (MySQL), 1883/9001 (MQTT), 5000 (Backend), 5173 (Frontend), 6379 (Redis)

### External Dependencies
- **MySQL 8.0** (or Docker container)
- **Eclipse Mosquitto** (MQTT Broker)
- **Redis 7** (for Celery/Caching)
- **SMTP Server** (for email alerts)
- **SMS Gateway** (optional, for SMS alerts)

---

## Development Deployment

### 1. Clone Repository
```bash
git clone https://github.com/vsp-2007/Textile-Production-and-Workforce-Management-Optimization-Platform.git
cd Textile-Production-and-Workforce-Management-Optimization-Platform
```

### 2. Configure Environment
```bash
# Backend
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Frontend
cp frontend/.env.example frontend/.env  # if exists
```

### 3. Start with Docker Compose
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Start with IoT simulator (for testing)
docker-compose --profile testing up -d
```

### 4. Initialize Database
```bash
# Run migrations
docker-compose exec backend flask db upgrade

# Seed initial data
docker-compose exec backend flask seed-db

# Create admin user (optional)
docker-compose exec backend flask create-admin
```

### 5. Access Applications
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5000/api
- **MQTT Broker**: localhost:1883 (WebSocket: localhost:9001)
- **Database**: localhost:3306 (user: texworkforce, db: texworkforce)

### 6. Demo Credentials
| Role | Employee ID | Password |
|------|-------------|----------|
| Admin | ADMIN001 | Admin@123 |
| Supervisor | SUPV001 | Supervisor@123 |
| Operator | OPR001 | Operator@123 |

---

## Production Deployment

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes
```

### 2. Configure Production Environment
```bash
# Create production environment file
cat > .env.production << EOF
# Database
MYSQL_ROOT_PASSWORD=your_strong_root_password
MYSQL_PASSWORD=your_strong_db_password

# Security
SECRET_KEY=your_very_long_random_secret_key_here
JWT_SECRET_KEY=your_very_long_random_jwt_secret_here
JWT_COOKIE_SECURE=True

# MQTT
MQTT_USERNAME=mqtt_user
MQTT_PASSWORD=strong_mqtt_password

# Redis
REDIS_PASSWORD=strong_redis_password

# Email/SMS
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USERNAME=alerts@yourdomain.com
SMTP_PASSWORD=your_smtp_password
SMS_GATEWAY_URL=https://api.yoursmsgateway.com
SMS_GATEWAY_KEY=your_sms_api_key

# Frontend
FRONTEND_URL=https://yourdomain.com
EOF
```

### 3. SSL/TLS Configuration (Production)
```bash
# Create SSL directory
mkdir -p nginx/ssl

# Add your certificates
# nginx/ssl/cert.pem
# nginx/ssl/key.pem

# Or use Let's Encrypt with certbot
sudo certbot certonly --standalone -d yourdomain.com
```

### 4. Production Docker Compose
```bash
# Use production override
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 5. Database Backup Strategy
```bash
# Create backup script
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T mysql mysqldump -u root -p$MYSQL_ROOT_PASSWORD texworkforce > backups/texworkforce_$DATE.sql
gzip backups/texworkforce_$DATE.sql
# Keep only last 30 days
find backups/ -name "*.sql.gz" -mtime +30 -delete
EOF

chmod +x backup.sh

# Add to crontab (daily at 2 AM)
# 0 2 * * * /path/to/backup.sh
```

### 6. Monitoring & Health Checks
```bash
# Check service health
docker-compose ps

# View logs
docker-compose logs --tail=100 backend
docker-compose logs --tail=100 frontend

# Health check endpoints
curl http://localhost:5000/health
curl http://localhost:5173/health
```

---

## Manual Deployment (Without Docker)

### Backend
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/texworkforce
export JWT_SECRET_KEY=your-secret
export MQTT_BROKER_HOST=localhost
# ... other vars

# Run migrations
flask db upgrade

# Seed data
flask seed-db

# Run with Gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --threads 2 --timeout 120 run:app
```

### Frontend
```bash
cd frontend

# Install dependencies
npm ci

# Build for production
npm run build

# Serve with nginx or serve
npx serve -s dist -l 5173
```

### Systemd Services
```ini
# /etc/systemd/system/texworkforce-backend.service
[Unit]
Description=TexWorkforce Backend
After=network.target mysql.service redis.service

[Service]
Type=exec
User=texworkforce
WorkingDirectory=/opt/texworkforce/backend
Environment=FLASK_ENV=production
ExecStart=/opt/texworkforce/backend/venv/bin/gunicorn --bind 0.0.0.0:5000 --workers 4 run:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/texworkforce-frontend.service
[Unit]
Description=TexWorkforce Frontend
After=network.target

[Service]
Type=exec
User=texworkforce
WorkingDirectory=/opt/texworkforce/frontend
ExecStart=/usr/bin/npx serve -s dist -l 5173
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Configuration Reference

### Backend Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `FLASK_ENV` | No | development | Environment mode |
| `SECRET_KEY` | Yes | - | Flask secret key |
| `DATABASE_URL` | Yes | - | MySQL connection string |
| `JWT_SECRET_KEY` | Yes | - | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | No | 3600 | Access token expiry (seconds) |
| `JWT_COOKIE_SECURE` | No | False | Secure cookies (True for HTTPS) |
| `MQTT_BROKER_HOST` | No | localhost | MQTT broker hostname |
| `MQTT_BROKER_PORT` | No | 1883 | MQTT broker port |
| `MQTT_USERNAME` | No | - | MQTT username |
| `MQTT_PASSWORD` | No | - | MQTT password |
| `CELERY_BROKER_URL` | No | redis://localhost:6379/0 | Celery broker |
| `SMTP_HOST` | No | - | SMTP server |
| `SMS_GATEWAY_URL` | No | - | SMS API endpoint |

### Frontend Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_API_URL` | No | http://localhost:5000/api | Backend API URL |
| `VITE_WS_URL` | No | http://localhost:5000 | WebSocket URL |

---

## Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check MySQL is running
docker-compose ps mysql

# Check logs
docker-compose logs mysql

# Verify credentials
docker-compose exec mysql mysql -u texworkforce -p texworkforce
```

#### MQTT Connection Issues
```bash
# Test MQTT connection
mosquitto_pub -h localhost -t test -m "hello"
mosquitto_sub -h localhost -t test

# Check Mosquitto logs
docker-compose logs mosquitto
```

#### WebSocket Not Connecting
- Ensure `JWT_COOKIE_SECURE=False` in development
- Check CORS settings in backend
- Verify WebSocket URL in frontend config

#### Frontend Build Errors
```bash
# Clear cache and rebuild
cd frontend
rm -rf node_modules package-lock.json dist
npm install
npm run build
```

#### Permission Denied (Docker)
```bash
# Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

---

## Scaling Considerations

### Horizontal Scaling
- **Backend**: Run multiple instances behind load balancer
- **Frontend**: Static files served by CDN/nginx
- **Database**: Read replicas for reporting queries
- **MQTT**: Cluster Mosquitto or use EMQX
- **Redis**: Redis Cluster for session/cache

### Performance Tuning
- **MySQL**: Increase `innodb_buffer_pool_size` (70% RAM)
- **Gunicorn**: Workers = 2×CPU cores, threads = 2-4
- **Redis**: Enable persistence for sessions
- **MQTT**: QoS 1 for critical messages, QoS 0 for telemetry

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong JWT secrets (64+ chars)
- [ ] Enable HTTPS/TLS in production
- [ ] Set `JWT_COOKIE_SECURE=True`
- [ ] Configure CORS for specific domains
- [ ] Enable MySQL SSL connections
- [ ] Set up MQTT authentication
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Regular security updates
- [ ] Backup encryption

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/vsp-2007/Textile-Production-and-Workforce-Management-Optimization-Platform/issues
- Documentation: See `docs/` folder
- API Spec: `docs/API_SPEC.md`