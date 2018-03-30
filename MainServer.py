from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from datetime import datetime
from sys import stdout
from Team import Team
from allVars import *
from serverVars import *
import utils
import json
from threading import Timer


class TeamServerSideProtocol(NetstringReceiver):

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

        # Set timer and password attempts for user authentication
        self.auth_t = Timer(LOGIN_TIMEOUT, self.denyTeam, args=('Timed out. ', ))
        self.auth_t.start()
        self.triesLeft = PASSWORD_TRIES


    def stringReceived(self, line):
        '''
        Called when line/message is received from team. We usually check the start of the line to decide what to do.
        '''

        # Get message and log it.
        team_id = self.factory.protocols[self]
        message = line.decode()
        self.factory.writeToLogFromTeam(message, team_id)

        # deserialize message
        message = json.loads(message)

        # Team Authentication
        if message['type'] == 'auth':
            team_id = self.processAuthentication(message)

        # Team is trying to send a message without our approval.
        elif team_id is None or not self.factory.teams[team_id].isLoggedIn():
            self.writeToTeam({
                'type'  : 'response',
                'result': 'error',
                'msg'   : 'Please login first.'
            })

        # Team is logged in. We can accept data.
        else:
            # Team is sending drone state information, accept it and store it.
            if message['type'] == 'drone-state':
                timestamp = message['timestamp']
                for state in message['states']:
                    drone_id = state['drone_id']
                    self.factory.teams[team_id].upateDroneState(drone_id, state, timestamp)
            elif message['type'] == 'logout':
                self.factory.teams[team_id].logOut()
                self.writeToTeam({
                    'type': 'response',
                    'result': 'success'
                })
            elif message['type'] == 'bid-response':
                pass
            elif message['type'] == 'task-response':
                pass

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
        self.writeToTeam({
            'type'  : 'response',
            'result': 'error',
            'msg'   : reason
        })
        self.transport.loseConnection()

    def writeToTeam(self, message):
        '''
        Writes to the team assigned to this protocol, and logs the message.
        :param dict message
        '''
        team_id = self.factory.protocols[self]
        self.factory.writeToLogToTeam(json.dumps(message), team_id)
        self.sendString(json.dumps(message).encode())

    def processAuthentication(self, message):
        '''
        Run all logic for authenticating and 'logging in' a user.
        '''
        team_id, password = message["team-id"], message["password"]
        if self.factory.teams[team_id].isLoggedIn():
            self.writeToTeam({
                'type'  : 'response',
                'result': 'error',
                'msg'   : 'Team ' + team_id + ' is already logged in.'
            })
        elif password != self.factory.passwords[team_id]:
            self.writeToTeam({
                'type': 'response',
                'result': 'error',
                'msg': 'Password error'
            })
            self.triesLeft -= 1
            if self.triesLeft == 0:
                self.denyTeam('Too many password attempts.')
        else:
            self.factory.teams[team_id].approveLogin()
            self.factory.protocols[self] = team_id
            self.writeToTeam({
                'type': 'response',
                'result': 'success'
            })
            self.auth_t.cancel()


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
