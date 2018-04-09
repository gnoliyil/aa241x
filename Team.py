from Drone import Drone
from allVars import *

class Team():
    def __init__(self, team_id, password):
        self.team_id = team_id
        self.password = password
        self.protocol = None
        self.drones = [Drone(team_id, str(drone_id)) for drone_id in range(NUM_DRONES)]
        self.loggedIn = False

    def setProtocol(self, protocol):
        self.protocol = protocol

    def tryLogin(self, password):
        if password == self.password:
            self.loggedIn = True
            return True
        else:
            return False

    def isLoggedIn(self):
        return self.loggedIn

    def logOut(self):
        self.protocol = None
        self.loggedIn = False

    def upateDroneState(self, drone_id, state, timestamp):
        self.drones[int(drone_id)].updateState(state, timestamp)
