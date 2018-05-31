

class Drone():
    def __init__(self, team_id, drone_id, db):
        self.drone_id = drone_id
        self.team_id = team_id
        self.db = db
        self.insertIntoDB()

    def insertIntoDB(self):
        '''
        Initialize drone in DB if drone is not in DB.
        If drone_id == 0 it means it is the physical drone.
        '''
        is_physical = True if self.drone_id == 0 else False
        with self.db:
            result = self.db.query_one('SELECT COUNT(*) FROM Drones  \
                                      WHERE team_id = %s AND drone_id = %s;',
                                      (self.team_id, self.drone_id))
            if result is not None:
                in_db = result[0]
            else:
                raise Exception('Query failed while inserting drone into DB.')

            if not in_db:
                self.db.query_one('INSERT INTO Drones VALUES (%s, %s, %s);',
                              (self.team_id, self.drone_id, is_physical))

    def updateState(self, state, timestamp):
        '''
        Insert new state into database. Return true if success.
        '''
        # TODO: not tested yet
        with self.db:
            result = self.db.query_one('INSERT INTO Drone_States_History (team_id,drone_id, \
            	               time_stamp,longitude,latitude,altitude,velocity,k_passengers,\
                                battery_left,state,next_port,fulfilling)  \
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING record_id;',
                              (self.team_id, self.drone_id, timestamp, state['longitude'],
                                state['latitude'],state['altitude'],str(state['velocity']),
                                state['k_passengers'],state['battery_left'],state['state'],
                                state['fulfilling'],state['next_port']))
            record_id = result['record_id']

            result = self.db.query_one('SELECT * FROM Drone_States WHERE team_id = %s AND drone_id = %s',
                                       (self.team_id, self.drone_id))
            if result is None:
                self.db.insert_values('Drone_States', (self.team_id, self.drone_id, record_id), ('team_id', 'drone_id', 'record_id'))
            else:
                self.db.query_one('UPDATE Drone_States SET record_id = %s WHERE team_id = %s AND drone_id = %s',
                                  (record_id, self.team_id, self.drone_id))


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
                                           WHERE team_id = %s AND drone_id = %s);', (self.team_id, self.drone_id))
        state['velocity'] = eval(state['velocity']) # convert string back to array
        print(state)
        return state
