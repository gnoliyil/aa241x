from Drone import Drone
from allVars import *

class Team():
    def __init__(self, team_id):
        self.team_id = team_id
        self.protocol = None
        self.drones = [Drone(team_id, i) for i in range(NUM_DRONES)]
        self.startedLogin = False
        self.loggedIn = False

    def setProtocol(self, protocol):
        self.protocol = protocol

    def startLogin(self):
        self.startedLogin = True

    def hasStartedLogin(self):
        return self.startedLogin

    def approveLogin(self):
        self.loggedIn = True

    def isLoggedIn(self):
        return self.loggedIn

    def logOut(self):
        self.protocol = None
        self.startedLogin = False
        self.loggedIn = False
