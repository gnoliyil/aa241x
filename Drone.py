class DroneState:
    def __init__(self):
        pass

    def fromDict(self, d):
        self.drone_id = d.get('drone_id')
        self.type     = d.get('type')
        self.longitude= d.get('longitude')
        self.latitude = d.get('latitude')
        self.altitude = d.get('altitude')
        self.velocity = d.get('velocity')
        self.pax      = d.get('pax')
        self.drone_state = d.get('drone-state')

class Drone():
    def __init__(self, team_id, drone_id):
        self.drone_id = drone_id
        self.team_id = team_id
        self.state = None  # State: (longitude, latitude, altitute) #TODO: update state tuple
        self.lastUpdated = None

    def updateState(self, state, timestamp):
        self.state = DroneState()
        self.state.fromDict({
            'drone_id': self.drone_id,
            'type'    : state['type'],
            'longitude': state['longitude'],
            'latitude': state['latitude'],
            'altitude': state['altitude'],
            'velocity': state['velocity'],
            'pax'     : state['pax'],
            'drone-state': state['drone-state']
        })
        self.lastUpdated = timestamp
        # TODO: store current state to database (or in MainServer.py)

    def getMostRecentState(self):
        return self.state
