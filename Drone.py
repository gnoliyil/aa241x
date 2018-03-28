
class Drone():
    def __init__(self, team_id, drone_id):
        self.drone_id = drone_id
        self.team_id = team_id
        self.lastState = None
        self.states = []  # State: (longitude, latitude, altitute) #TODO: update state tuple

    def updateState(self, state):
        self.lastState = state
        self.states.append(state)
        print('Drone ' + self.drone_id + ' of Team ' + self.team_id + ' last state is: ' + str(state))

    def getMostRecentState(self):
        return self.lastState
