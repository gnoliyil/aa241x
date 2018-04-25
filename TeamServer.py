from twisted.internet import reactor, defer
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.internet.protocol import Protocol, ReconnectingClientFactory, ProcessProtocol
from sys import stdout
import threading
from allVars import *
from clientVars import *
import utils
import datetime
import json

from stateSimulator import Simulator  # TODO: delete when we stop using simulator.


class TeamClientSideProtocol(NetstringReceiver):

    def __init__(self):
        self.clientState = 'INIT'
        self.droneStates = []  # TODO: This is just a placeholder list for simulation purposes. This assumes there is only one drone per team right now.

    #---------------TWISTED PROTOCOL METHODS----------------------------------#

    def stringReceived(self, line):
        '''
        Called when we receive a line/message from the main server.
        '''
        message = json.loads(line.decode())
        print('[SERVER] ', message)

        if message['type'] == 'response':
            if self.clientState == 'LOGGING-IN':
                if message['result'] == 'success':
                    self.clientState = 'LOGGED-IN'
                    self.startSimulation()
                    self.sendDroneState()
                else:
                    self.connectionLost()


    def connectionMade(self):
        '''
        Called when a connection with the main server has been established.
        '''
        print('Connection with SERVER established.')
        # TODO: change to config file later
        team_id, password = CLIENT_USERNAME, CLIENT_PASSWORD
        self.writeToServer({
            'type': 'auth',
            'team-id': team_id,
            'password': password
        })
        self.clientState = 'LOGGING-IN'

    #---------------COMMUNICATION METHODS-------------------------------------#

    def writeToServer(self, message):
        '''
        Write message to main server.
        '''
        print('[TO SERVER] ', message)
        self.sendString(json.dumps(message).encode())

    #-------------------------------------------------------------------------#

    def startSimulation(self):
        '''
        Current drone SKD simulator call, which will add state data to our queue from a different
        thread.
        '''
        for drone_id in range(NUM_DRONES):
            simulator = Simulator(self.droneStates, drone_id)
            t = threading.Thread(target=simulator.run, args=(self.factory.run_event, ))
            t.start()
            self.factory.threads.append(t)


    def sendDroneState(self):
        '''
        Important method. Send drone state to main server every DRONE_UPDATE_INTERVAL seconds.
        We call reactor reactor.callLater() to recall the method on the set interval.
        '''
        if self.droneStates:
            lastState = self.droneStates[-1]
            drone_id = '0' # TODO; 0 is just a placeholder
            self.writeToServer({
                'type': 'drone-state',
                'timestamp': datetime.datetime.now().timestamp(),
                'states': [{
                    'drone_id': 0,
                    'type'    : lastState['type'],
                    'longitude': lastState['longitude'],
                    'latitude': lastState['latitude'],
                    'altitude': lastState['altitude'],
                    'velocity': lastState['velocity'],
                    'pax'     : lastState['pax'],
                    'drone-state': lastState['drone-state']
                }]
            })
            self.droneStates.clear()
        reactor.callLater(DRONE_UPDATE_INTERVAL, self.sendDroneState)



# Need factory so we can reconnect. Factory maintains should mantain persistent state.
class TeamFactory(ReconnectingClientFactory):

    def __init__(self):
        '''
        Initialize variables:
            threads: list of all threads that we start, so we can kill them if need be
            run_event: signal to communicate with threads. Usefull calls: .set(), .isSet(), or .clear()
        '''
        self.threads = []
        self.run_event = threading.Event()

    #---------------TWISTED FACTORY METHODS----------------------------------#

    # Standard for Twisted. This is the protocol that the factory will be initializing.
    protocol = TeamClientSideProtocol

    def startedConnecting(self, connector):
        '''
        Called when team tries to connect with server.
        '''
        print('Trying to connect.')


    def clientConnectionLost(self, connector, reason):
        '''
        Called when a client (in this case there is only one) loses connection to the server.
        '''
        print('Lost connection.  Reason:', reason)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)


    def clientConnectionFailed(self, connector, reason):
        '''
        Called if connection with client fails.
        '''
        print('[ERROR: CONNECTION FAILED]: ', reason)
        ReconnectingClientFactory.clientConnectionFailed(self, connector,
                                                         reason)

    def startFactory(self):
        '''
        Factory pre-processing: set event thread so they can run.
        '''
        self.run_event.set()

    def stopFactory(self):
        '''
        Factory shutdown: tell threads to stop running and join them.
        '''
        self.run_event.clear()
        for t in self.threads:
            t.join()
        self.threads.clear()

def main():
    '''
    Main function: Connect to server and run the reactor. Standard for Twisted.
    '''
    host = 'localhost'
    port = 8007
    reactor.connectTCP(host, port, TeamFactory())
    reactor.run()

if __name__ == '__main__':
    main()
