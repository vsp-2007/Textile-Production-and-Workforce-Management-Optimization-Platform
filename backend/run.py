import os
from app import create_app, socketio, db
from app.models import *

app = create_app(os.environ.get('FLASK_ENV', 'development'))

# Initialize MQTT client
from app.services.mqtt_client import mqtt_client
mqtt_client.init_app(app)

if __name__ == '__main__':
    # Run with SocketIO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=app.config.get('DEBUG', True),
        allow_unsafe_werkzeug=True
    )