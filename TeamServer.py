from twisted.internet import reactor, defer
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.internet.protocol import Protocol, ReconnectingClientFactory, ProcessProtocol
import team_vars as tv
import threading, datetime, json, sys

from Simulator import Simulator  # TODO: delete when we stop using simulator.


class TeamClientSideProtocol(NetstringReceiver):

    def __init__(self):
        self.droneStates = [[] for _ in range(tv.NUM_DRONES)]

    #---------------TWISTED PROTOCOL METHODS----------------------------------#

    def stringReceived(self, line):
        '''
        Called when we receive a line/message from the main server.
        '''
        message = json.loads(line.decode())
        print('[FROM SERVER] ', message)
        print()

        if message['type'] == 'response':
            if self.clientState == 'LOGGING-IN':
                if message['result'] == 'success':
                    self.clientState = 'LOGGED-IN'
                    self.addToDroneStates()
                    for drone_id in range(tv.NUM_DRONES):
                        self.sendDroneState(drone_id)

        elif message['type'] == 'request':
            request = message['request']
            self.decideBid(request)

        elif message['type'] == 'bid_result':
            if 'result' == 'win':
                task = message['task']
                request_id = message['request_id']
                status = 'confirm' if self.confirmTask(task) else 'deny'
                self.writeToServer({
                  'type': 'task_update',
                  'request_id': request_id,
                  'status': 'status',
                  'msg': None
                })
            else:
                self.handleBidDenied()


    def connectionMade(self):
        '''
        Called when a connection with the main server has been established. Tries to log in to the server.
        '''
        print('Connection with SERVER established.')
        self.writeToServer({
            'type': 'auth',
            'team_id': self.factory.team_id,
            'password': self.factory.password
        })
        self.clientState = 'LOGGING-IN'

    #---------------COMMUNICATION METHODS-------------------------------------#

    def writeToServer(self, message):
        '''
        Write message to main server.
        '''
        print('[TO SERVER] ', message)
        self.sendString(json.dumps(message).encode())

    #------------------------OUR METHODS-------------------------------------#

    def startSimulation(self):
        '''
        Current drone SKD simulator call, which will add state data to our queue from a different
        thread.
        '''
        for drone_id in range(tv.NUM_DRONES):
            simulator = Simulator(self.droneStates[drone_id], drone_id)
            t = threading.Thread(target=simulator.run, args=(self.factory.run_event,))
            t.start()
            self.factory.threads.append(t)

    def sendDroneState(self, drone_id):
        '''
        Important method. Send drone state to main server every DRONE_UPDATE_INTERVAL seconds.
        We call reactor reactor.callLater() to recall the method on the set interval.
        '''
        if self.droneStates[drone_id]:
            lastState = self.droneStates[drone_id][-1]
            self.writeToServer({
                'type': 'drone_state',
                'drone_state': {
                    'drone_id': lastState['drone_id'],
                    'longitude': lastState['longitude'],
                    'latitude': lastState['latitude'],
                    'altitude': lastState['altitude'],
                    'velocity': lastState['velocity'],
                    'k_passengers': lastState['k_passengers'],
                    'battery_left': lastState['battery_left'],
                    'state': lastState['state'],
                    'fulfilling': lastState['fulfilling'],
                    'next_port': lastState['next_port']
                }
            })
            self.droneStates[drone_id].clear()
        reactor.callLater(tv.DRONE_UPDATE_INTERVAL, self.sendDroneState, drone_id)

    #------------------------METHOD TO IMPLEMENT-------------------------------#

    def decideBid(self, request):
        '''
        Important method. Decides if we want to submit a bid to the given request.
        '''
        request_id = request['request_id']
        k_passengers = request['k_passengers']
        price_expected = request['expected_price']
        from_port = request['from_port']
        to_port = request['to_port']
        #######################TODO FOR TEAM###################################
        # 1) Implement this function with your own algorithm for deciding how
        # much to bid. This should take into account price and ETA,
        # and k_passengers. We currently
        # use our own dummy function that bids the expected_price.
        ######################################################################
        wantToBid = True  # TODO: decide if you want to bid.
        if wantToBid:
            drone_id = 0            # TODO: decide what drone to use
            seconds_expected = 120     # TODO: Calculate expected time of trip, in seconds.
            price = price_expected  # TODO: decide your price.
        ######################################################################
        if wantToBid:
            message = { 'type': 'bid',
              'bid': {
                 'request_id': request_id,
                 'accepted': True,
                 'drone_id': drone_id,
                 'seconds_expected': seconds_expected,
                 'price': price
              }
            }
        else:
            message = { 'type': 'bid',
              'bid': {
                 'request_id': request_id,
                 'accepted': False,
                 'drone_id': None,
                 'seconds_expected': None,
                 'price': None
              }
            }
        self.writeToServer(message)


    def addToDroneStates(self):
        #######################TODO FOR TEAM###################################
        # 2) Implement a function that has the same functionality as
        # startSimulation/Simulator, but with real drone data. You need to append
        # drone state data from every drone drone_id to self.droneStates[drone_id],
        # like we do in the Simulator. Please use that as a reference. Our
        # sendDroneState function takes care of sending the data to the
        # MainServer.
        #
        # Once you start writing this you can comment out all the simulation
        # code, but make sure you have it as a reference.
        ######################################################################
        # self.startSimulation() # TODO uncomment to see simulation functionality
        pass
        ######################################################################

    def confirmTask():
        '''
        Return True if we will try to fulfill the given task and False if we will not.
        '''
        #######################TODO FOR TEAM###################################
        # Implement this function with your own decision making. You must decide
        # if you will attempt at fulfilling the task. The team will be penalized
        # if you do not, since you submitted a bid. Fill 'confirm' with
        # True or False based on your drone status and any other factor.
        ######################################################################
        confirm = True # TODO you decide the actual value for this.
        ######################################################################
        return confirm

    def handleBidDenied():
        '''
        This function is called when you submitted a bid but you lost it.
        '''
        #######################TODO FOR TEAM###################################
        # Implement this function. You probably want to upodate your drone information.
        # For example, if you submitted a bid with drone_id 0, that drone was unable to
        # submit any other bids until now. You need to keep track of that.
        ######################################################################
        pass
        ######################################################################



# Need factory so we can reconnect. Factory maintains should mantain persistent state.
class TeamFactory(ReconnectingClientFactory):

    def __init__(self, team_id, password):
        '''
        Initialize variables:
            threads: list of all threads that we start, so we can kill them if need be
            run_event: signal to communicate with threads. Usefull calls: .set(), .isSet(), or .clear()
        '''
        self.threads = []
        self.run_event = threading.Event()
        self.team_id = team_id
        self.password = password

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
    if len(sys.argv) != 3:
        print('Syntax: {} <team_id> <password>'.format(sys.argv[0]))
        sys.exit(0)

    (team_id, password) = sys.argv[1:]
    host = 'localhost'
    port = 8007
    reactor.connectTCP(host, port, TeamFactory(team_id, password))
    reactor.run()

if __name__ == '__main__':
    main()
