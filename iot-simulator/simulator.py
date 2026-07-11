import paho.mqtt.client as mqtt
import json
import time
import random
import threading
import signal
import sys
from datetime import datetime
from typing import Dict, List
import os

class MachineSimulator:
    def __init__(self, broker_host='localhost', broker_port=1883, topic_prefix='texworkforce'):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        
        # Machine configurations
        self.machines = [
            {
                'machine_code': 'RSF-01',
                'name': 'Ring Spinning Frame 1',
                'type': 'spinning',
                'base_rpm': 15000,
                'base_temp': 35,
                'base_vibration': 1.2,
                'base_output': 50,
                'status': 'active'
            },
            {
                'machine_code': 'RSF-02',
                'name': 'Ring Spinning Frame 2',
                'type': 'spinning',
                'base_rpm': 15000,
                'base_temp': 35,
                'base_vibration': 1.2,
                'base_output': 50,
                'status': 'active'
            },
            {
                'machine_code': 'RSF-03',
                'name': 'Ring Spinning Frame 3',
                'type': 'spinning',
                'base_rpm': 15000,
                'base_temp': 35,
                'base_vibration': 1.2,
                'base_output': 50,
                'status': 'idle'
            },
            {
                'machine_code': 'AJL-01',
                'name': 'Air Jet Loom 1',
                'type': 'weaving',
                'base_rpm': 800,
                'base_temp': 40,
                'base_vibration': 2.5,
                'base_output': 20,
                'status': 'active'
            },
            {
                'machine_code': 'AJL-02',
                'name': 'Air Jet Loom 2',
                'type': 'weaving',
                'base_rpm': 800,
                'base_temp': 40,
                'base_vibration': 2.5,
                'base_output': 20,
                'status': 'active'
            },
            {
                'machine_code': 'AJL-03',
                'name': 'Air Jet Loom 3',
                'type': 'weaving',
                'base_rpm': 800,
                'base_temp': 40,
                'base_vibration': 2.5,
                'base_output': 20,
                'status': 'maintenance'
            },
            {
                'machine_code': 'RPL-01',
                'name': 'Rapier Loom 1',
                'type': 'weaving',
                'base_rpm': 600,
                'base_temp': 38,
                'base_vibration': 3.0,
                'base_output': 18,
                'status': 'active'
            },
            {
                'machine_code': 'RPL-02',
                'name': 'Rapier Loom 2',
                'type': 'weaving',
                'base_rpm': 600,
                'base_temp': 38,
                'base_vibration': 3.0,
                'base_output': 18,
                'status': 'idle'
            },
            {
                'machine_code': 'JQL-01',
                'name': 'Jacquard Loom 1',
                'type': 'weaving',
                'base_rpm': 400,
                'base_temp': 42,
                'base_vibration': 4.0,
                'base_output': 12,
                'status': 'active'
            },
            {
                'machine_code': 'JQL-02',
                'name': 'Jacquard Loom 2',
                'type': 'weaving',
                'base_rpm': 400,
                'base_temp': 42,
                'base_vibration': 4.0,
                'base_output': 12,
                'status': 'fault'
            },
            {
                'machine_code': 'WDM-01',
                'name': 'Winch Dyeing Machine 1',
                'type': 'dyeing',
                'base_rpm': 50,
                'base_temp': 95,
                'base_vibration': 0.5,
                'base_output': 100,
                'status': 'active'
            },
            {
                'machine_code': 'JDM-01',
                'name': 'Jet Dyeing Machine 1',
                'type': 'dyeing',
                'base_rpm': 100,
                'base_temp': 130,
                'base_vibration': 1.0,
                'base_output': 80,
                'status': 'active'
            },
            {
                'machine_code': 'STF-01',
                'name': 'Stenter Frame 1',
                'type': 'finishing',
                'base_rpm': 200,
                'base_temp': 180,
                'base_vibration': 0.8,
                'base_output': 150,
                'status': 'active'
            }
        ]
        
        self.client = None
        self.running = False
        self.simulation_interval = int(os.environ.get('SIMULATION_INTERVAL', 5))
        self.fault_probability = 0.02  # 2% chance per interval
        self.recovery_probability = 0.1  # 10% chance per interval
        
    def connect(self):
        """Connect to MQTT broker"""
        self.client = mqtt.Client(
            client_id=f'iot-simulator-{random.randint(1000, 9999)}',
            clean_session=True
        )
        
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            print(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            return True
        except Exception as e:
            print(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("MQTT connected successfully")
        else:
            print(f"MQTT connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        print(f"MQTT disconnected with code {rc}")
    
    def on_publish(self, client, userdata, mid):
        pass  # print(f"Message {mid} published")
    
    def generate_telemetry(self, machine: Dict) -> Dict:
        """Generate realistic telemetry data for a machine"""
        status = machine['status']
        
        # Add some randomness to base values
        rpm = max(0, machine['base_rpm'] + random.uniform(-100, 100))
        temp = max(0, machine['base_temp'] + random.uniform(-3, 3))
        vibration = max(0, machine['base_vibration'] + random.uniform(-0.3, 0.3))
        
        # Output depends on status
        if status == 'active':
            output = max(0, machine['base_output'] + random.uniform(-5, 5))
            error_code = None
        elif status == 'idle':
            output = 0
            error_code = None
        elif status == 'maintenance':
            output = 0
            error_code = None
        elif status == 'fault':
            output = 0
            # Generate realistic error codes
            error_codes = ['YARN_BREAK', 'WEFT_BREAK', 'WARP_BREAK', 'TEMP_HIGH', 'VIBRATION_HIGH', 'MOTOR_FAULT', 'SENSOR_FAULT']
            error_code = random.choice(error_codes)
        else:  # offline
            output = 0
            error_code = 'CONNECTION_LOST'
        
        return {
            'machine_code': machine['machine_code'],
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'status': status,
            'rpm': round(rpm, 1),
            'temperature': round(temp, 1),
            'vibration': round(vibration, 2),
            'output_count': int(output),
            'error_code': error_code,
            'raw_payload': {
                'sensor_1': round(random.uniform(0, 100), 2),
                'sensor_2': round(random.uniform(0, 100), 2),
                'sensor_3': round(random.uniform(0, 100), 2)
            }
        }
    
    def maybe_change_status(self, machine: Dict):
        """Randomly change machine status based on probabilities"""
        if machine['status'] == 'active':
            if random.random() < self.fault_probability:
                # Machine develops a fault
                machine['status'] = 'fault'
                print(f"⚠️  {machine['machine_code']} developed a fault!")
            elif random.random() < 0.01:  # 1% chance to go idle
                machine['status'] = 'idle'
                print(f"💤 {machine['machine_code']} went idle")
        elif machine['status'] == 'fault':
            if random.random() < self.recovery_probability:
                machine['status'] = 'active'
                print(f"✅ {machine['machine_code']} recovered from fault")
        elif machine['status'] == 'idle':
            if random.random() < 0.05:  # 5% chance to become active
                machine['status'] = 'active'
                print(f"▶️  {machine['machine_code']} started")
        elif machine['status'] == 'maintenance':
            if random.random() < 0.03:  # 3% chance maintenance completes
                machine['status'] = 'idle'
                print(f"🔧 {machine['machine_code']} maintenance completed")
    
    def publish_telemetry(self, machine: Dict, telemetry: Dict):
        """Publish telemetry to MQTT"""
        topic = f"{self.topic_prefix}/machines/{machine['machine_code']}/telemetry"
        payload = json.dumps(telemetry)
        
        result = self.client.publish(topic, payload, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            print(f"Failed to publish to {topic}: {result.rc}")
    
    def run_simulation(self):
        """Main simulation loop"""
        self.running = True
        print(f"Starting IoT simulation for {len(self.machines)} machines...")
        print(f"Publishing every {self.simulation_interval} seconds")
        print("Press Ctrl+C to stop\n")
        
        try:
            while self.running:
                for machine in self.machines:
                    # Maybe change status
                    self.maybe_change_status(machine)
                    
                    # Generate and publish telemetry
                    telemetry = self.generate_telemetry(machine)
                    self.publish_telemetry(machine, telemetry)
                    
                    # Log
                    status_emoji = {
                        'active': '🟢',
                        'idle': '🟡',
                        'maintenance': '🔵',
                        'fault': '🔴',
                        'offline': '⚫'
                    }.get(machine['status'], '⚪')
                    
                    print(f"{status_emoji} {machine['machine_code']}: {machine['status'].upper()} | "
                          f"RPM: {telemetry['rpm']:.0f} | "
                          f"Temp: {telemetry['temperature']:.1f}°C | "
                          f"Vib: {telemetry['vibration']:.2f}mm/s | "
                          f"Output: {telemetry['output_count']} yds"
                          + (f" | ERROR: {telemetry['error_code']}" if telemetry['error_code'] else ""))
                
                print("-" * 80)
                time.sleep(self.simulation_interval)
                
        except KeyboardInterrupt:
            print("\nStopping simulation...")
            self.stop()
    
    def stop(self):
        """Stop the simulation"""
        self.running = False
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
        print("Simulation stopped")

def main():
    broker_host = os.environ.get('MQTT_BROKER_HOST', 'localhost')
    broker_port = int(os.environ.get('MQTT_BROKER_PORT', 1883))
    topic_prefix = os.environ.get('MQTT_TOPIC_PREFIX', 'texworkforce')
    interval = int(os.environ.get('SIMULATION_INTERVAL', 5))
    
    simulator = MachineSimulator(
        broker_host=broker_host,
        broker_port=broker_port,
        topic_prefix=topic_prefix
    )
    simulator.simulation_interval = interval
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        simulator.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    if simulator.connect():
        simulator.run_simulation()
    else:
        print("Failed to start simulator")
        sys.exit(1)

if __name__ == '__main__':
    main()