
class Drone():
    def __init__(self, drone_id, team_id):
        self.drone_id = drone_id
        self.team_id = team_id
        self.states = []  # State: (longitude, latitude, altitute) #TODO: update state tuple

    def updateState(self, state):
        self.states.append(state)

    def getMostRecentState(self):
        return self.states[-1]
