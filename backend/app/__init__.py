from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_cors import CORS
from celery import Celery

from app.config import config

# Extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
socketio = SocketIO(cors_allowed_origins="*")
celery = Celery(__name__)


def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    socketio.init_app(app, async_mode=app.config['SOCKETIO_ASYNC_MODE'])
    CORS(app, supports_credentials=True)
    
    # Celery config
    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],
        task_serializer='json',
        accept_content=['json'],
        result_serializer='json',
        timezone='UTC',
        enable_utc=True,
    )
    
    # Register blueprints
    from app.api.auth import auth_bp
    from app.api.machines import machines_bp
    from app.api.operators import operators_bp
    from app.api.shifts import shifts_bp
    from app.api.reallocation import reallocation_bp
    from app.api.reports import reports_bp
    from app.api.alerts import alerts_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(machines_bp, url_prefix='/api/machines')
    app.register_blueprint(operators_bp, url_prefix='/api/operators')
    app.register_blueprint(shifts_bp, url_prefix='/api/shifts')
    app.register_blueprint(reallocation_bp, url_prefix='/api/reallocation')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    
    # Register WebSocket handlers
    from app.websocket.handlers import register_websocket_handlers
    register_websocket_handlers(socketio)
    
    # Register CLI commands
    from app.cli import register_cli_commands
    register_cli_commands(app)
    
    # Health check
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'texworkforce-api'}
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app


import os