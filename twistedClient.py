from twisted.internet import reactor, defer
from twisted.protocols.basic import LineReceiver
from twisted.internet.protocol import Protocol, ReconnectingClientFactory, ProcessProtocol

from sys import stdout
from stateSimulator import Simulator

from threading import Thread
from allVars import *


class TeamClientProtocol(LineReceiver):

    def __init__(self):
        self.connected = False  # TODO: decide if we need this.
        self.teamID = None
        self.authenticated = False
        self.droneStates = []


    def lineReceived(self, line):
        message = line.decode()
        if message.startswith(AUTH):
            self.respondTo(message)
        else:
            print('[SERVER] ' + message)

    def connectionMade(self):
        self.connected = True
        #d = self.startCommuncation()
        #d.addCallback(self.startCommuncation)
        self.startSimulation()
        d1 = self.sendDroneState()
        d1.addCallback(self.sendDroneState)

    def connectionLost(self, reason):
        self.connected = False
        print("Connection lost.")
        reactor.stop()

    #---------------METHODS ABOVE ARE PROTOCOL ONES-----------------------------

    def writeToMain(self, message):
        # self.transport is also automatically set, use to send data to client
        self.transport.write(message.encode())

    # TODO: delete?
    def startCommuncation(self):
        d = defer.Deferred()
        message = input("Send message to main server: ")
        if message == 'quit':
            return
        self.sendLine(message.encode())
        reactor.callLater(.1, self.startCommuncation)
        return d

    def startSimulation(self):
        simulator = Simulator(self.droneStates)
        #t = Thread(target=simulator.run)
        #t.start()
        # TODO: implement killing thread when connection is lost.

    def sendDroneState(self):
        d = defer.Deferred()
        if self.droneStates:
            self.sendLine(str(self.droneStates[-1]).encode())
        self.droneStates.clear()
        reactor.callLater(3, self.sendDroneState)
        return d

    # TODO: Try to figure out how to get async user input if needed?
    def respondTo(self, message):
        response = input(message)
        self.sendLine(str(message + response).encode())



# Need factory so we can reconnect. Factory maintains should mantain persistent state.
class TeamFactory(ReconnectingClientFactory):
    def startedConnecting(self, connector):
        print('Started to connect.')

    def buildProtocol(self, addr):
        print('Connected. (Resetting reconnection delay)')
        print(addr)
        self.resetDelay()
        return TeamClientProtocol()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection.  Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        print('Connection failed. Reason:', reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)



reactor.connectTCP("localhost", 8007, TeamFactory())
reactor.run()
