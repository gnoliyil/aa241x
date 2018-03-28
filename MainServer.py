from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from datetime import datetime
from sys import stdout
from Team import Team
from allVars import *
from serverVars import *
import utils
from threading import Timer


class TeamServerSideProtocol(LineReceiver):

    #-----------------TWISTED PROTOCOL METHODS--------------------------------#

    def connectionMade(self):
        '''
        Called when a conenction is made with a team for the first time.
        Update relevant variables and start authentication process.
        Note: self.factory was set by the factory's default buildProtocol
        '''
        self.factory.protocols[self] = None
        self.factory.numProtocols += 1
        self.factory.writeToLog('Connection made. There are currently %d open connections.' % (self.factory.numProtocols,))
        self.writeToTeam(TEAM_ID_QUERY)

        # Set timer and password attempts for user authentication
        self.auth_t = Timer(LOGIN_TIMEOUT, self.denyTeam, args=('Timed out. ', ))
        self.auth_t.start()
        self.triesLeft = PASSWORD_TRIES


    def lineReceived(self, line):
        '''
        Called when line/message is received from team. We usually check the start of the line to decide what to do.
        '''

        # Get message and log it.
        team_id = self.factory.protocols[self]
        message = line.decode()
        self.factory.writeToLogFromTeam(message, team_id)

        # Team Authentication
        if message.startswith(AUTH):
            team_id = self.processAuthentication(message)

        # Team is trying to send a message without our approval.
        elif team_id is None or not self.factory.teams[team_id].isLoggedIn():
            self.writeToTeam('You are not authorized to send data yet. Please complete authentication.')

        # Team is logged in. We can accept data.
        else:

            # Team is sending drone state information, accept it and store it.
            if message.startswith(DRONE_UPDATE):
                match = utils.matchDroneUpdate(message)
                if match:
                    drone_id, longitude, latitude, altitude = match.groups()
                    state = (longitude, latitude, altitude)
                    self.factory.teams[team_id].upateDroneState(drone_id, state)


    def connectionLost(self, reason):
        '''
        Called when connection to team is lost. Update relevant variables and clean up data structures so team can log in again.
        '''
        self.factory.numProtocols -= 1
        self.factory.writeToLog('Connection lost. There are currently %d open connections.' % (self.factory.numProtocols,))
        team_id = self.factory.protocols[self]
        self.auth_t.cancel()
        if team_id is not None:
            self.factory.teams[team_id].logOut()
            self.factory.protocols[self] = None
            self.factory.writeToLog('Team ' + team_id + ' logged out.')

    #-------------------------------------------------------------------------#

    def denyTeam(self, reason):
        '''
        Close connection with user for given reason
        '''
        self.writeToTeam('Login failed. ' + reason + ' Losing connection.')
        self.transport.loseConnection()

    def writeToTeam(self, message):
        '''
        Writes to the team assigned to this protocol, and logs the message.
        '''
        team_id = self.factory.protocols[self]
        self.factory.writeToLogToTeam(message, team_id)
        self.sendLine(message.encode())


    def processAuthentication(self, message):
        '''
        Run all logic for authenticating and 'logging in' a user.
        '''
        if message.startswith(TEAM_ID_QUERY):
            match = utils.matchIntResponse(TEAM_ID_QUERY, message)
            if match:
                team_id_try = match[1]

                # Invalid team registration
                if team_id_try not in self.factory.teams:
                    self.writeToTeam('Team ' + team_id_try + ' is not registered.')
                    self.writeToTeam(TEAM_ID_QUERY)
                elif team_id_try in self.factory.teams and self.factory.teams[team_id_try].isLoggedIn():
                    self.writeToTeam('Team ' + team_id_try + ' is already logged in.')
                    self.writeToTeam(TEAM_ID_QUERY)
                elif team_id_try in self.factory.teams and self.factory.teams[team_id_try].hasStartedLogin():
                    self.writeToTeam('Team ' + team_id_try + ' already started login.')
                    self.writeToTeam(TEAM_ID_QUERY)


                # Valid team registration (not authorize yet), set protocol and startedLogin and ask for password
                else:
                    team_id = team_id_try
                    self.factory.protocols[self] = team_id
                    self.factory.teams[team_id].startLogin()
                    self.factory.teams[team_id].setProtocol(self)
                    self.writeToTeam(PASSWORD_QUERY)
                    return team_id

            else:
                self.writeToTeam('Wrong format.')
                self.writeToTeam(TEAM_ID_QUERY)

        elif message.startswith(PASSWORD_QUERY):
            team_id = self.factory.protocols[self]

            # Successful authentication, let team know, stop auth timer thread.
            if team_id is not None and utils.matchExactString(PASSWORD_QUERY, self.factory.passwords[team_id], message):
                self.factory.teams[team_id].approveLogin()
                self.writeToTeam(AUTH_SUCCESS + 'Team ' + team_id + ': Success! You are now logged in.')
                self.auth_t.cancel()

            # Unsuccessful authentication attempt
            else:
                if team_id is None:
                    self.writeToTeam('Invalid: We need your team ID first.')
                else:
                    self.writeToTeam('Wrong password.')
                    self.triesLeft -= 1
                    if self.triesLeft == 0:
                        self.denyTeam('Too many password attempts.')
                        return
                self.writeToTeam(PASSWORD_QUERY)



class MainFactory(ServerFactory):

    def __init__(self):
        '''
        Initializes variables:
            numProtocols: number of open protocols
            protocols: maps { protocol: team_id }
            teams: maps { team: Team object }
            passwords: maps { team_id : password }
        '''
        self.numProtocols = 0
        self.protocols = {}
        self.teams = { str(i) : Team(str(i)) for i in range(NUM_TEAMS)}  # Maps team_id to Team object.
        self.passwords = { str(i): 't' + str(i) for i in range(NUM_TEAMS)} # TODO: make a file and load from it.

    #---------------TWISTED FACTORY METHODS----------------------------------#

    # This will be used by the default buildProtocol to create new protocols:
    protocol = TeamServerSideProtocol

    # Called when factory is initialized (put code other than variable initiation here)
    def startFactory(self):
        '''
        Called when factory starts running. Sets isRunning to true for logging. Opens files.
        '''
        self.isRunning = True
        self.log = open(LOG_NAME, 'a')
        self.log.write('Starting new log: ' + str(datetime.now()) + '\n')

    # Factory shutdown
    def stopFactory(self):
        '''
        Called when factory is shutting down. Set isRunning to false so we can log without errors, and closes opened files.
        '''
        self.isRunning = False
        self.log.write('\n')
        self.log.close()

    #---------------LOGGING METHODS-------------------------------------------#

    def writeToLog(self, message):
        '''
        Prints message to output and writes message to log.
        '''
        if self.isRunning:
            print('[SERVER] ' + message)
            self.log.write('[SERVER]' + message + '\n')

    def writeToLogFromTeam(self, message, team_id):
        '''
        Prints to output and writes to log a message that we received from Team team_id
        '''
        if self.isRunning:
            if team_id is None:
                print('[UNKNOWN TEAM] ' + message)
                self.log.write('[UNKNOWN TEAM]' + message + '\n')
            else:
                print('[TEAM ' + team_id + '] ' + message)
                self.log.write('[TEAM ' + team_id + '] ' + message + '\n')

    def writeToLogToTeam(self, message, team_id):
        '''
        HELPER FUNCTION FOR COMMUNICATION: DON'T USE OTHERWISE
        Prints message that we server sends to Team team_id, and also writes that to the log.
        '''
        if self.isRunning:
            if team_id is None:
                print('[SERVER TO UNKNOWN TEAM] ' + message)
                self.log.write('[SERVER TO UNKNOWN TEAM]' + message + '\n')
            else:
                print('[SERVER TO TEAM ' + team_id + '] ' + message)
                self.log.write('[SERVER TO TEAM ' + team_id + '] ' + message + '\n')

    #-------------------------------------------------------------------------#



# 8007 is the port you want to run under. Choose something >1024
def main():
    endpoint = TCP4ServerEndpoint(reactor, 8007)
    endpoint.listen(MainFactory())
    reactor.run()


if __name__ == '__main__':
    main()
