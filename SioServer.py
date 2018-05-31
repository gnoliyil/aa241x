import socketio
import eventlet
import threading
from flask import Flask, render_template

class SioServer:
    def __init__(self, droneStates):
        self.droneStates = droneStates

        self.sio = socketio.Server()
        self.app = Flask(__name__)
        self.flask_app = socketio.Middleware(self.sio, self.app)

        self.sid_to_device = {}
        self.device_to_sid = {}

        self.sio.on('connect', self.connect)
        self.sio.on('disconnect', self.disconnect)
        self.sio.on('set device id', self.set_device_id)
        self.sio.on('drone state', self.on_drone_state)
        self.sio.on('arrival', self.on_arrival)

    def connect(self, sid, environ):
        self.sid_to_device[sid] = None

    def disconnect(self, sid, environ):
        try:
            deviceId = self.sid_to_device[sid]
            del self.device_to_sid[deviceId]
            del self.sid_to_device[sid]
        except KeyError:
            pass

    def set_device_id(self, sid, data):
        deviceId = data["device_id"]
        self.sid_to_device[sid] = deviceId
        self.device_to_sid[deviceId] = sid

    def on_drone_state(self, sid, data):
        deviceId = self.sid_to_device[sid]

        state = {
            'drone_id': deviceId,
            'latitude': data['latitude'],
            'longitude': data['longitude'],
            'altitude': data['altitude'],
            'velocity': data['velocity'],
            'battery_left': data['battery_left'],
        }
        self.droneStates[deviceId].update(state)


    def send_waypoint(self, device_id, data):
        sid = self.device_to_sid[device_id]

        destination = data['destination']
        velocity = data['velocity']
        self.sio.emit('command', {
            'destination': destination,
            'velocity': velocity
        }, room=sid)

if __name__ == '__main__':
    # wrap Flask application with socketio's middleware
    sio_server = SioServer()

    # deploy as an eventlet WSGI server
    eventlet.wsgi.server(eventlet.listen(('', 9090)), sio_server.flask_app)

