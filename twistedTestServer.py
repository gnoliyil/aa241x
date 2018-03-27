from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from datetime import datetime
from sys import stdout
from Team import Team
from allVars import *
import utils


class TeamProtocol(LineReceiver):
    '''
    Potentially useful calls:
    self.transport.loseConnection()
    '''

    def connectionMade(self):
        # self.factory was set by the factory's default buildProtocol
        self.factory.protocols[self] = None
        self.factory.numProtocols += 1
        self.factory.writeToLog('Connection made. There are currently %d open connections.\n' % (self.factory.numProtocols,))
        self.writeToTeam(TEAM_ID_QUERY)


    def lineReceived(self, line):
        team_id = self.factory.protocols[self]
        message = line.decode()
        self.factory.writeToLogFromClient(message, team_id)
        if message == "write to all":
            self.sendToAllTeams("hi all")

        # Team Communication Authentication
        elif message.startswith(AUTH):
            team_id = self.processAuthentication(message)
        elif team_id is None or not self.teams[team_id].isAuthenticated:
            self.writeToTeam('You are not authorized to send data yet. Please complete authentication.')
        else:
            print('[CLIENT]: ' + message)


    def connectionLost(self, reason):
        self.factory.numProtocols -= 1
        self.factory.writeToLog('Connection lost. There are currently %d open connections.\n' % (self.factory.numProtocols,))
        # Clean up team and authentication when connection is lost

    def writeToTeam(self, message):
        team_id = self.factory.protocols[self]
        self.factory.writeToLogToTeam(message, team_id)
        self.sendLine(message.encode())


    def sendToAllTeams(self, message):
        for team in self.factory.protocols:
            if team != self:
                team.transport.write(message.encode())


    def processAuthentication(self, message):
        if message.startswith(TEAM_ID_QUERY):
            match = utils.matchIntResponse(TEAM_ID_QUERY, message)
            if match:
                team_id_try = match[1]

                # Invalid team registration
                if team_id_try not in self.factory.passwords:
                    self.writeToTeam('Team does not exist.')
                    self.writeToTeam(TEAM_ID_QUERY)
                elif team_id_try in self.factory.teams:
                    self.writeToTeam(str('Team ' + team_id_try + ' already started registration.'))  # TODO: string builder and encoder
                    self.writeToTeam(TEAM_ID_QUERY)

                # Valid team registration (not authorize yet), add to database
                else:
                    team_id = team_id_try
                    self.factory.protocols[self] = team_id
                    self.factory.teams[team_id] = Team(self, team_id)
                    self.writeToTeam(PASSWORD_QUERY)  # Start password auth
                    return team_id

            else:
                self.writeToTeam('Wrong format.')
                self.writeToTeam(TEAM_ID_QUERY)

        elif message.startswith(PASSWORD_QUERY):
            team_id = self.factory.protocols[self]

            # Successful authentication
            if team_id is not None and utils.matchExactString(PASSWORD_QUERY, self.factory.passwords[team_id], message):
                self.factory.teams[team_id].authenticate()
                self.writeToTeam('Team ' + team_id + ': You have been authenticated.')

            # Unsuccessful authentication attempt
            else:
                if team_id is None:
                    self.writeToTeam('Invalid: We need your team ID first.')
                else:
                    self.writeToTeam('Wrong password.')  # TODO: be more rigorous in password responses? Not really necessary.
                self.writeToTeam(PASSWORD_QUERY)



class MainFactory(ServerFactory):

    # This will be used by the default buildProtocol to create new protocols:
    protocol = TeamProtocol

    def __init__(self, logName='log.txt'):
        self.isRrunning = True
        self.numProtocols = 0
        self.logName = logName
        self.protocols = {}  # Maps protocol to team_id
        self.teams = {}  # Maps team_id to Team object
        self.passwords = {'1': 't1', '2': 't2', '3': 't3'}

    # Called when factory is initialized (put code other than variable initiation here)
    def startFactory(self):
        self.log = open(self.logName, 'a')
        self.log.write('Starting new log: ' + str(datetime.now()) + '\n')

    # Factory shutdown
    def stopFactory(self):
        self.isRrunning = False
        self.log.write('\n')
        for team_id, protocol in self.teams:
            self.sendLine(str('Hi team ' + team_id))
        self.log.close()

    def writeToLog(self, message):
        if self.isRrunning:
            print('[SERVER]: ' + message)
            self.log.write('[SERVER]' + message)

    def writeToLogFromClient(self, message, team_id):
        if self.isRrunning:
            if team_id is None:
                print('[UNKNOWN TEAM] ' + message)
                self.log.write('[UNKNOWN TEAM]' + message)
            else:
                print('[TEAM ' + team_id + '] ' + message)
                self.log.write('[TEAM ' + team_id + '] ' + message)

    def writeToLogToTeam(self, message, team_id):
        if self.isRrunning:
            if team_id is None:
                print('[SERVER TO UNKNOWN TEAM] ' + message)
                self.log.write('[SERVER TO UNKNOWN TEAM]' + message)
            else:
                print('[SERVER TO TEAM ' + team_id + '] ' + message)
                self.log.write('[SERVER TO TEAM ' + team_id + '] ' + message)



# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
endpoint.listen(MainFactory())
reactor.run()
