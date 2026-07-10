import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime
from flask import current_app

from app import db, socketio
from app.models import Machine, MachineStatus, MachineTelemetry, MachineDowntime, Alert, AlertType, AlertSeverity, User


class MQTTClient:
    def __init__(self):
        self.client = None
        self.connected = False
        self.app = None
    
    def init_app(self, app):
        self.app = app
        self.client = mqtt.Client(
            client_id=f"texworkforce-{app.config.get('MQTT_CLIENT_ID', 'backend')}",
            clean_session=True
        )
        
        # Set callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        
        # Set credentials if provided
        username = app.config.get('MQTT_USERNAME')
        password = app.config.get('MQTT_PASSWORD')
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Connect
        try:
            host = app.config.get('MQTT_BROKER_HOST', 'localhost')
            port = app.config.get('MQTT_BROKER_PORT', 1883)
            keepalive = app.config.get('MQTT_KEEPALIVE', 60)
            
            self.client.connect_async(host, port, keepalive)
            self.client.loop_start()
        except Exception as e:
            app.logger.error(f"MQTT connection failed: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            topic_prefix = self.app.config.get('MQTT_TOPIC_PREFIX', 'texworkforce')
            # Subscribe to machine telemetry topics
            client.subscribe(f"{topic_prefix}/machines/+/telemetry")
            client.subscribe(f"{topic_prefix}/machines/+/status")
            client.subscribe(f"{topic_prefix}/+/telemetry")
            current_app.logger.info("MQTT connected and subscribed")
        else:
            current_app.logger.error(f"MQTT connection failed with code {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        current_app.logger.warning(f"MQTT disconnected with code {rc}")
    
    def _on_subscribe(self, client, userdata, mid, granted_qos):
        current_app.logger.debug(f"MQTT subscribed: {mid}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode('utf-8'))
            
            # Extract machine code from topic
            # Format: texworkforce/machines/{machine_code}/telemetry
            parts = topic.split('/')
            if len(parts) >= 3 and parts[1] == 'machines':
                machine_code = parts[2]
                self._process_telemetry(machine_code, payload)
            elif len(parts) >= 2:
                machine_code = parts[1]
                self._process_telemetry(machine_code, payload)
                
        except json.JSONDecodeError:
            current_app.logger.error(f"Invalid JSON in MQTT message: {msg.payload}")
        except Exception as e:
            current_app.logger.error(f"Error processing MQTT message: {e}")
    
    def _process_telemetry(self, machine_code, payload):
        """Process machine telemetry data"""
        with self.app.app_context():
            machine = Machine.query.filter_by(machine_code=machine_code.upper()).first()
            if not machine:
                current_app.logger.warning(f"Unknown machine: {machine_code}")
                return
            
            # Update machine status
            status_str = payload.get('status', 'active').lower()
            try:
                new_status = MachineStatus(status_str)
            except ValueError:
                new_status = MachineStatus.ACTIVE
            
            old_status = machine.status
            machine.status = new_status
            machine.last_telemetry_at = datetime.utcnow()
            
            # Create telemetry record
            telemetry = MachineTelemetry(
                machine_id=machine.id,
                status=new_status,
                rpm=payload.get('rpm'),
                temperature=payload.get('temperature'),
                vibration=payload.get('vibration'),
                output_count=payload.get('output_count'),
                error_code=payload.get('error_code'),
                raw_payload=payload
            )
            db.session.add(telemetry)
            
            # Handle downtime tracking
            if old_status == MachineStatus.ACTIVE and new_status in [MachineStatus.FAULT, MachineStatus.OFFLINE, MachineStatus.MAINTENANCE]:
                downtime = MachineDowntime(
                    machine_id=machine.id,
                    start_time=datetime.utcnow(),
                    reason=payload.get('reason') or f'Status changed to {new_status.value}',
                    reported_by=None  # System reported
                )
                db.session.add(downtime)
            elif old_status in [MachineStatus.FAULT, MachineStatus.OFFLINE, MachineStatus.MAINTENANCE] and new_status == MachineStatus.ACTIVE:
                open_downtime = MachineDowntime.query.filter_by(
                    machine_id=machine.id, end_time=None
                ).first()
                if open_downtime:
                    open_downtime.end_time = datetime.utcnow()
                    open_downtime.resolved_by = None
                    open_downtime.duration_minutes = int(
                        (open_downtime.end_time - open_downtime.start_time).total_seconds() / 60
                    )
            
            # Create alerts for critical statuses
            if new_status == MachineStatus.FAULT:
                alert = Alert(
                    alert_type=AlertType.MACHINE_FAULT,
                    severity=AlertSeverity.CRITICAL,
                    machine_id=machine.id,
                    message=f'Machine {machine.machine_code} ({machine.name}) reported fault: {payload.get("error_code", "Unknown error")}'
                )
                db.session.add(alert)
            elif new_status == MachineStatus.IDLE and old_status == MachineStatus.ACTIVE:
                alert = Alert(
                    alert_type=AlertType.MACHINE_IDLE,
                    severity=AlertSeverity.WARNING,
                    machine_id=machine.id,
                    message=f'Machine {machine.machine_code} ({machine.name}) is idle (no operator assigned)'
                )
                db.session.add(alert)
            
            # Check for maintenance due
            if machine.last_maintenance and machine.maintenance_interval_hours:
                hours_since_maintenance = (datetime.utcnow() - machine.last_maintenance).total_seconds() / 3600
                if hours_since_maintenance >= machine.maintenance_interval_hours:
                    alert = Alert(
                        alert_type=AlertType.MAINTENANCE_DUE,
                        severity=AlertSeverity.WARNING,
                        machine_id=machine.id,
                        message=f'Machine {machine.machine_code} ({machine.name}) maintenance due ({hours_since_maintenance:.1f}h since last maintenance)'
                    )
                    db.session.add(alert)
            
            db.session.commit()
            
            # Emit real-time update to WebSocket clients
            socketio.emit('machine_telemetry', {
                'machine_id': machine.id,
                'machine_code': machine.machine_code,
                'name': machine.name,
                'status': new_status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'telemetry': telemetry.to_dict()
            }, room='supervisors')
            
            current_app.logger.debug(f"Processed telemetry for {machine_code}: {new_status.value}")
    
    def publish(self, topic, payload, qos=1):
        """Publish message to MQTT broker"""
        if not self.connected:
            current_app.logger.warning("MQTT not connected, cannot publish")
            return False
        
        try:
            result = self.client.publish(topic, json.dumps(payload), qos=qos)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            current_app.logger.error(f"MQTT publish failed: {e}")
            return False
    
    def subscribe(self, topic, qos=1):
        """Subscribe to a topic"""
        if self.connected:
            self.client.subscribe(topic, qos)
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()


# Global instance
mqtt_client = MQTTClient()