from Drone import Drone
from allVars import *

class Team():
    def __init__(self, team_id, password, db):
        self.db = db
        self.team_id = team_id
        self.password = password
        self.protocol = None
        self.drones = [Drone(team_id, str(drone_id)) for drone_id in range(NUM_DRONES)]

    def tryLogin(self, password, protocol):
        if password == self.password:
            self.protocol = protocol
            with self.db:
                self.db.query_list('UPDATE Teams SET is_logged_in = TRUE WHERE team_id = %s;', (self.team_id,))
            return True
        else:
            return False

    def isLoggedIn(self):
        with self.db:
            return self.db.query_one('SELECT is_logged_in FROM Teams WHERE team_id = %s;', (self.team_id,))[0]

    def logOut(self):
        self.protocol = None
        with self.db:
            self.db.query_list('UPDATE Teams SET is_logged_in = FALSE WHERE team_id = %s;', (self.team_id,))

    def upateDroneState(self, drone_id, state, timestamp):
        self.drones[int(drone_id)].updateState(state, timestamp)
