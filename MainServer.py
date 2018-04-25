from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from datetime import datetime
from sys import stdout
from Team import Team
from allVars import *
from serverVars import *
from keys import *
import utils
import json
from threading import Timer
from db import DBHandler


class TeamServerSideProtocol(NetstringReceiver):

    # -----------------TWISTED PROTOCOL METHODS--------------------------------#

    def connectionMade(self):
        '''
        Called when a conenction is made with a team for the first time.
        Update relevant variables and start authentication process.
        Note: self.factory was set by the factory's default buildProtocol
        '''
        self.db = self.factory.db

        self.factory.protocols[self] = None
        self.factory.numProtocols += 1
        self.factory.writeToLog(
            'Connection made. There are currently %d open connections.' % (self.factory.numProtocols,))

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
                'type': 'response',
                'result': 'error',
                'msg': 'Please login first.'
            })

        # Team is logged in. We can accept data.
        else:
            # Team is sending drone state information, accept it and store it.
            # TODO: try-catch if info is formatted wrongfully or incomplete
            if message['type'] == 'drone-state':
                timestamp = message['timestamp']
                for state in message['states']:
                    drone_id = state['drone_id']
                    self.factory.teams[team_id].upateDroneState(drone_id, state, timestamp)
                self.writeToTeam({
                    'type': 'response',
                    'result': 'success'
                })
            elif message['type'] == 'logout':
                self.factory.logOutTeam()
                self.writeToTeam({
                    'type': 'response',
                    'result': 'success'
                })
            elif message['type'] == 'bid-response':
                # TODO: implement
                pass
            elif message['type'] == 'task-response':
                # TODO: implement
                pass

    def connectionLost(self, reason):
        '''
        Called when connection to team is lost. Update relevant variables and clean up data structures so team can log in again.
        '''
        # Log out team.
        team_id = self.factory.protocols[self]
        self.factory.logOutTeam(self, team_id)

        # Lower number of protocols.
        self.factory.numProtocols -= 1
        self.factory.writeToLog(
            'Connection lost. There are currently %d open connections.' % (self.factory.numProtocols,))
        self.factory.protocols[self] = None

    # -------------------------------------------------------------------------#

    def denyTeam(self, reason):
        '''
        Close connection with user for given reason
        '''
        self.writeToTeam({
            'type': 'response',
            'result': 'error',
            'msg': reason
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
        if team_id not in self.factory.teams:
            self.denyTeam('Team {} not found'.format(team_id))

        elif self.factory.teams[team_id].isLoggedIn():
            self.denyTeam('Team ' + team_id + ' is already logged in.')

        elif not self.factory.teams[team_id].tryLogin(password, self):
            self.denyTeam('Password error.')

        else:
            self.factory.protocols[self] = team_id
            with self.db:
                self.db.query_list('UPDATE Teams SET is_logged_in = TRUE WHERE team_id = %s;', (team_id, ))
            self.writeToTeam({
                'type': 'response',
                'result': 'success'
            })
            # self.auth_t.cancel()
            with self.db:
                self.db.query_list('UPDATE Teams SET is_logged_in = TRUE WHERE team_id = %s;', (team_id,))


class MainFactory(ServerFactory):

    def __init__(self):
        '''
        Initializes variables:
            numProtocols: number of open protocols
            protocols: maps { protocol: team_id }
            teams: maps { team: Team object }
            passwords: maps { team_id : password }
        '''
        self.db = DBHandler(DB_NAME, DB_USER, DB_PASSWORD)
        self.numProtocols = 0
        self.protocols = {}
        self.requestCallId = {}
        self._loadTeams()

    def _loadTeams(self):
        with self.db:
            teams = self.db.query_list('SELECT * FROM Teams;')
            self.db.query_list('UPDATE Teams SET is_logged_in = FALSE;')  # reset all login states
        self.teams = {team['team_id']: Team(team['team_id'], team['password']) for team in teams}

    # ---------------TWISTED FACTORY METHODS----------------------------------#

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

    # ---------------LOGGING METHODS-------------------------------------------#

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

    # -------------------------------------------------------------------------#

    def logOutTeam(self, protocol, team_id):
        if team_id is not None:
            self.teams[team_id].logOut()
            with self.db:
                self.db.query_list('UPDATE Teams SET is_logged_in = FALSE WHERE team_id = %s;', (team_id,))
            self.writeToLog('Team ' + team_id + ' logged out.')

    def sendTask(self, team_id, request_id):
        with self.db:
            request = self.db.query_one('SELECT * FROM requests WHERE request_id = %s', (request_id))
        if request is None:
            self.writeToLog('[ERROR] Not exist [REQ# {}]'.format(request_id))
            return

        task_generated = {
            'type': 'task',
            'request_id': request['request_id'],
            'k_passengers': request['k_passengers'],
            'time_requested': request['time_requested'],
            'time_expected': request['time_expected'],
            'price_expected': request['price_expected'],
            'from_port': request['from_port'],
            'to_port': request['to_port'],
        }

        for protocol in self.factory.protocols:
            if self.factory.protocols[protocol] == team_id:
                protocol.writeToTeam(task_generated)

    def broadcastRequest(self, request_id):
        with self.db:
            request = self.db.query_one('SELECT * FROM requests WHERE request_id = %s', (request_id))
        if request is None:
            self.writeToLog('[ERROR] Not exist [REQ# {}]'.format(request_id))
            return

        request_generated = {
            'type': 'request',
            'request': {
                'request_id': request['request_id'],
                'k_passengers': request['k_passengers'],
                'time_requested': request['time_requested'],
                'time_expected': request['time_expected'],
                'price_expected': request['price_expected'],
                'from_port': request['from_port'],
                'to_port': request['to_port'],
            }
        }

        # team connected
        for protocol in self.factory.protocols:
            protocol.writeToTeam(request_generated)
        callId = reactor.callLater(REQUEST_TIMEOUT, self.bidTimeOut, (request['request_id'],))
        self.requestCallId[request['request_id']] = callId
        with self.db:
            self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                              ('REQUEST_SENT', request['request_id']))

    def bidTimeOut(self, request_id):
        self.writeToLog("[BID TIMEOUT] [request_id = {}]".format(request_id))
        with self.db:
            self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;', ('BID_COMPLETED', request_id))
        self.collectBid(request_id)

    def selectBestBid(self, request_id, bids):
        # dummy function now
        return bids[0]

    def collectBid(self, request_id):
        # collect bids
        # finds the best bid
        with self.db:
            bids_accepted = self.db.query_list('SELECT * FROM Bids WHERE request_id = %s AND accepted = TRUE;',
                                               (request_id,))

            if len(bids_accepted) == 0:
                # no bids accepted
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                  ('BID_COMPLETED_FAIL', request_id))
                self.writeToLog('[REQUEST FAILED] No accepted bids for [REQ# {}]'.format(request_id))
            else:
                # there exist some bids
                best_bid = self.selectBestBid(request_id, bids_accepted)
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;'
                                  'UPDATE Bids SET succeeded = %s WHERE bid_id = %s;',
                                  ('BID_COMPLETED_SUCCESS', request_id, True, best_bid['bid_id']))

                self.writeToLog('[REQUEST SUCCEEDED] Accept bids [BID# {}, TEAM# {}, REQ# {}]'
                                .format(best_bid['bid_id'], best_bid['team_id'], request_id))
                self.sendTask(best_bid['team_id'], request_id)

    # ---------------------------------------------------------------

    def onReceiveDroneState(self, team_id, drone_states, timestamp = datetime.now()):
        drone_ids = [state['drone_id'] for state in drone_states]
        if len(set(drone_ids)) != len(drone_ids):
            self.writeToLog("[ERROR DUPLICATED DRONES] [TEAM# {}]".format(team_id))
            return

        for state in drone_states:
            state_kv = [
                ('team_id', team_id),
                ('drone_id', state['drone_id']),
                ('time_stamp', timestamp),
                ('battery_left', state['battery_left']),
                ('k_passengers', state['k_passengers']),
                ('latitude', state['latitude']),
                ('longitude', state['longitude']),
                ('altitude', state['altitude']),
                ('velocity', state['velocity']),
                ('from_port', state['from_port']),
                ('to_port', state['to_port']),
                ('fulfilling', state['fulfilling']),
            ]
            keys, values = zip(*state_kv)
            with self.db:
                try:
                    record_id = self.db.insert_values('Drone_States_History', values, keys)['record_id']
                except:
                    self.writeToLog('[ERROR WRITING DRONE_STATES] [TEAM# {} DRONE# {}]'.format(team_id, state['drone_id']))
                    return

                self.db.query_one('UPDATE drone_states SET record_id = %s WHERE (team_id, drone_id) = (%s, %s);',
                                  (record_id, team_id, state['drone_id']))


    def onRecieveTaskResponse(self, task_response):
        request_id = task_response['request_id']
        team_id = task_response['team_id']

    def onReceiveBid(self, bid):
        # check the request state
        # store bid in database
        # if all bids for a request are received, collect bid at once
        request_id = bid['request_id']
        team_id = bid['team_id']
        try:
            with self.db:
                request = self.db.query_list('SELECT * FROM requests WHERE request_id = %s', (request_id,))[0]
        except:
            self.writeToLog("[ERROR ON RECEIVING BID] Key error [request_id = {}]".format(request_id))
            return

        if request['state'] == 'INIT':
            # already time out
            # TODO: send error message
            self.writeToLog("[ERROR ON RECEIVING BID] Already timeout [TEAM# {}, REQ# {}]" \
                            .format(team_id, request_id))
            return
        if request['state'] == 'REQUEST_SENT' or request['state'] == 'BID_RECEIVED':
            with self.db:
                # store bid into database
                is_exists = self.db.count('Bids', 'request_id = %s AND team_id = %s', (request_id, team_id))
                if is_exists:
                    # TODO: send error message
                    self.writeToLog('[ERROR ON RECEIVING BID] Bid already exists [TEAM# {1}, REQ# {0}]'
                                    .format(request_id, team_id))
                    return
                else:
                    bid_accepted = True if bid['accepted'] else False
                    self.db.insert_values('Bids',
                                          (DBHandler.DEFAULT, bid['price'], bid_accepted, False, team_id, request_id))

                # count number of bids
                n_bids = self.db.count('Bids', 'request_id = %s', (request_id,))
                if n_bids == self.numProtocols:
                    self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s; ',
                                      ('BID_COMPLETED', request_id))
                    self.writeToLog("[RECEIVING ALL BIDS] for [REQ# {}]".format(request_id))
                    self.requestCallId[request_id].cancel()
                    self.writeToLog("[TIMEOUT CALLBACK CANCELLED] for [REQ# {}]".format(request_id))

                    self.collectBid(request_id)  # process all bids
                else:
                    self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                      ('BID_RECEIVED', request_id))


# 8007 is the port you want to run under. Choose something >1024
def main():
    endpoint = TCP4ServerEndpoint(reactor, 8007)
    endpoint.listen(MainFactory())
    reactor.run()


if __name__ == '__main__':
    main()
