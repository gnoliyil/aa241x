
class Team():
    def __init__(self, protocol, team_id):
        self.team_id = team_id
        self.protocol = protocol
        self.drones = []
        self.authenticated = False

    def authenticate(self):
        self.authenticated = True

    def isAuthenticated(self):
        return self.authenticated
