

class Drone():
    def __init__(self, team_id, drone_id, db):
        self.drone_id = drone_id
        self.team_id = team_id
        self.state = None  # State: (longitude, latitude, altitute) #TODO: update state tuple
        self.lastUpdated = None
        self.db = db
        self.insertIntoDB()

    def insertIntoDB(self):
        '''
        Initialize drone in DB if drone is not in DB.
        If drone_id == 0 it means it is the physical drone.
        '''
        is_physical = True if self.drone_id == 0 else False
        with self.db:
            in_db = self.db.query_one('SELECT COUNT(*) FROM Drones  \
                                      WHERE team_id = %s AND drone_id = %s;',
                                      (self.team_id, self.drone_id))
            if not in_db:
                self.db.query_one('INSERT INTO Drones VALUES (%s, %s, %s);',
                              (self.team_id, self.drone_id, is_physical))

    def updateState(self, state, timestamp):
        '''
        Insert new state into database. Return true if success.
        '''
        with self.db:
            success =  self.db.query_one('INSERT INTO Drone_States_History (team_id,drone_id, \
            	               time_stamp,longitude,latitude,altitude,velocity,k_passengers,\
                                battery_left,state,next_port,fulfilling)  \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);',
                              (self.team_id, self.drone_id, timestamp, state['longitude'],
                                state['latitude'],state['altitude'],str(state['velocity']),
                                state['k_passengers'],state['battery_left'],state['state'],
                                state['fulfilling'],state['next_port']))


    # TODO: test this function
    def getMostRecentState(self):
        '''
        Retrieves most recent state of drone from database.
        '''
        with self.db:
            state = self.db.query_one('SELECT *                       \
                                       FROM Drone_States_History      \
                                       WHERE record_id =              \
                                          (SELECT MAX(record_id)      \
                                           FROM Drone_States_History  \
                                           WHERE team_id = %s AND drone_id = %s);')
        print(state)
        return state
