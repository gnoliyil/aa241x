from Drone import Drone
from allVars import *


class Team():
    '''
    Team object. When dealing with Teams, MainServer should deal with teams through
    this class. This class has access to the DB.
    '''
    def __init__(self, team_id, password, db):
        self.db = db
        self.team_id = team_id
        self.password = password
        self.protocol = None
        self.drones = [Drone(team_id, drone_id, db) for drone_id in range(NUM_DRONES)]

    def tryLogin(self, password, protocol):
        '''
        Logs in team is password is correct. Returns True iff login is successful.
        '''
        if password == self.password:
            self.protocol = protocol
            with self.db:
                self.db.query_list('UPDATE Teams SET is_logged_in = TRUE WHERE team_id = %s;', (self.team_id,))
            return True
        else:
            return False

    def isLoggedIn(self):
        '''
        Returns True is team is logged in.
        '''
        with self.db:
            return self.db.query_one('SELECT is_logged_in FROM Teams WHERE team_id = %s;', (self.team_id,))


    def logOut(self):
        '''
        Logs team out.
        '''
        self.protocol.transport.loseConnection()
        self.protocol = None
        with self.db:
            self.db.query_list('UPDATE Teams SET is_logged_in = FALSE WHERE team_id = %s;', (self.team_id,))

    def upateDroneState(self, drone_id, state, timestamp):
        '''
        Updates drone state for specified drone.
        '''
        self.drones[int(drone_id)].updateState(state, timestamp)
