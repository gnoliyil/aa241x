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
        self.factory.writeToLog('Connection made. There are currently %d open connections.' % (self.factory.numProtocols,))
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
        elif team_id is None or not self.teams[team_id].isLoggedIn:
            self.writeToTeam('You are not authorized to send data yet. Please complete authentication.')



    def connectionLost(self, reason):
        self.factory.numProtocols -= 1
        self.factory.writeToLog('Connection lost. There are currently %d open connections.' % (self.factory.numProtocols,))
        team_id = self.factory.protocols[self]
        if team_id is not None:
            self.factory.teams[team_id].logOut()
            self.factory.protocols[self] = None
            self.factory.writeToLog('Team ' + team_id + ' logged out.')


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

            # Successful authentication
            if team_id is not None and utils.matchExactString(PASSWORD_QUERY, self.factory.passwords[team_id], message):
                self.factory.teams[team_id].approveLogin()
                self.writeToTeam('Team ' + team_id + ': Success! You are now logged in.')

            # Unsuccessful authentication attempt
            else:
                if team_id is None:
                    self.writeToTeam('Invalid: We need your team ID first.')
                else:
                    self.writeToTeam('Wrong password.')
                self.writeToTeam(PASSWORD_QUERY)



class MainFactory(ServerFactory):

    # This will be used by the default buildProtocol to create new protocols:
    protocol = TeamProtocol

    def __init__(self, logName='log.txt'):
        self.isRrunning = True
        self.numProtocols = 0
        self.logName = logName
        self.protocols = {}  # Maps protocol to team_id
        self.numTeams = 6
        self.teams = { str(i) : Team(i) for i in range(self.numTeams)}  # Maps team_id to Team object # TODO: initialize this from the start
        self.passwords = { str(i): 't' + str(i) for i in range(self.numTeams)} # TODO: make a file and load from it.

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

    #---------------LOGGING METHODS-------------------------------------------#

    def writeToLog(self, message):
        if self.isRrunning:
            print('[SERVER]: ' + message)
            self.log.write('[SERVER]' + message + '\n')

    def writeToLogFromClient(self, message, team_id):
        '''HELPER FUNCTION FOR COMMUNICATION: DON'T USE OTHERWISE'''
        if self.isRrunning:
            if team_id is None:
                print('[UNKNOWN TEAM] ' + message)
                self.log.write('[UNKNOWN TEAM]' + message + '\n')
            else:
                print('[TEAM ' + team_id + '] ' + message)
                self.log.write('[TEAM ' + team_id + '] ' + message + '\n')

    def writeToLogToTeam(self, message, team_id):
        '''HELPER FUNCTION FOR COMMUNICATION: DON'T USE OTHERWISE'''
        if self.isRrunning:
            if team_id is None:
                print('[SERVER TO UNKNOWN TEAM] ' + message)
                self.log.write('[SERVER TO UNKNOWN TEAM]' + message + '\n')
            else:
                print('[SERVER TO TEAM ' + team_id + '] ' + message)
                self.log.write('[SERVER TO TEAM ' + team_id + '] ' + message + '\n')

    #-------------------------------------------------------------------------#

    def initTeams(self):
        return


# 8007 is the port you want to run under. Choose something >1024
endpoint = TCP4ServerEndpoint(reactor, 8007)
endpoint.listen(MainFactory())
reactor.run()
