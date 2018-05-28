from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from datetime import datetime
from sys import stdout
from Team import Team
from allVars import *
from serverVars import *
from db import keys as k
import utils
import json
from db import DBHandler
import team_utils as tu
import log_utils as lu
import message_utils as mu
import attributes as atts
import traceback
import csv


# TODO in order:
# Finish bid broadcasting logic, add all requests to DB. Then use timestamps to set timers to send out bids. Make sure it works!
# Split logs per team. only print relevant stuff.
# Incorporate drone COMMUNICATION
# Make sure we can setup connection with other computer.

class TeamServerSideProtocol(NetstringReceiver):

    # -----------------TWISTED PROTOCOL METHODS--------------------------------#

    def connectionMade(self):
        '''
        Called when a conenction is made with a team for the first time.
        Update relevant variables and start authentication process.
        Note: self.factory was set by the factory's default buildProtocol
        '''
        self.db = self.factory.db

        # Remember we work with protocols. Every protocol is a connection
        self.factory.protocols[self] = None
        self.factory.numProtocols += 1
        lu.writeToLog(self.factory,
            'Connection made. There are currently %d open connections.' % (self.factory.numProtocols,))

    def connectionLost(self, reason):
        '''
        Called when connection to team is lost. Update relevant variables and clean up data structures so team can log in again.
        '''
        # Log out team.
        team_id = self.factory.protocols[self]
        tu.logOutTeam(self.factory, team_id)

        # Lower number of protocols.
        self.factory.numProtocols -= 1
        lu.writeToLog(self.factory,
            'Connection lost. There are currently %d open connections.' % (self.factory.numProtocols,))
        self.factory.protocols[self] = None

    def stringReceived(self, line):
        '''
        Called when line/message is received from team. Always check 'type' to decide what to do. Call
        methods from here but implement in MainFactory.
        '''
        try:
            # Get message and log it.
            team_id = self.factory.protocols[self]
            message = line.decode()
            lu.writeToLogFromTeam(self.factory, message, team_id)  # TODO: Have a separate log for each team.

            # deserialize message
            message = json.loads(message)

            # Check if message has 'type' attribute
            if not utils.hasattr(self, message, 'type'): return

            # Team Authentication
            if message['type'] == 'auth':
                tu.processAuthentication(self,message)
                return

            # Team is trying to send a message without our approval or before logging in.
            elif team_id is None or not self.factory.teams[team_id].isLoggedIn():
                tu.writeToTeam(self, mu.PLEASE_LOGIN_MSG)
                return

            # Team is logged in. We can accept data.
            else:
                # Team is sending drone state information, accept it and store it.
                if message['type'] == 'drone_state':
                    self.updateDroneState(team_id, message)

                # Team want to log out. Log them out.
                elif message['type'] == 'logout':
                    tu.logOutTeam(self.factory, team_id)

                elif message['type'] == 'bid-response':
                    # TODO: implement
                    pass
                elif message['type'] == 'task-response':
                    # TODO: implement
                    pass
        except Exception as e:
            lu.writeToLog(self.factory, '[ERROR] ' + str(e), verbose=False)
            print(traceback.format_exc())

    def updateDroneState(self, team_id, message):
        # Make sure message has all needed fields.
        if not utils.hasattr(self, message, 'drone_state'): return
        new_drone_state = message['drone_state']
        if not utils.hasattrs(self, new_drone_state, atts.DRONE_STATE_ATTRS): return

        # Try to insert state into DB. Write back result to team.
        try:
            success = self.factory.teams[team_id].upateDroneState(new_drone_state['drone_id'], new_drone_state, datetime.now())
            if success:
                tu.writeToTeam(self, mu.THANKS_MSG)
        except Exception as e:
            tu.writeToTeam(self, mu.ERROR_RESPONSE('DB error. Make sure all fields are correct. Error: {}'.format(e))) # Send error


class MainFactory(ServerFactory):

    def __init__(self):
        '''
        Initializes variables:
            numProtocols: number of open protocols
            protocols: maps { protocol: team_id }
            teams: maps { team: Team object }
            passwords: maps { team_id : password }
        '''
        self.db = DBHandler(k.DB_NAME, k.DB_USER, k.DB_PASSWORD)
        self.numProtocols = 0
        self.protocols = {}
        self.requestCallId = {}
        self._loadTeams()

    def _loadTeams(self):
        '''
        Load team info from DB and initialize team objects.
        '''
        with self.db:
            teams = self.db.query_list('SELECT * FROM Teams;')
            self.db.query_list('UPDATE Teams SET is_logged_in = FALSE;')  # reset all login states to logged out.
        self.teams = {team['team_id']: Team(team['team_id'], team['password'], self.db) for team in teams}

    # ---------------TWISTED FACTORY METHODS----------------------------------#

    # This will be used by the default buildProtocol to create new protocols:
    protocol = TeamServerSideProtocol

    def startFactory(self):
        '''
        Called when factory starts running. Sets isRunning to true for logging. Opens files.
        '''
        print('[SERVER] Factory started. Waiting for connections.')
        self.isRunning = True
        self.log = open(LOG_NAME, 'a')
        self.log.write('\nStarting new log: ' + str(datetime.now()) + '\n')

    def stopFactory(self):
        '''
        Called when factory is shutting down. Set isRunning to false so we can log without errors, and closes opened files.
        '''
        self.isRunning = False
        self.log.write('Stopping factory. \n')
        self.log.close()

    # -------------------------------------------------------------------------#

    def sendBidResults():
        # TODO: Implemnet this function. Send results to teams that did not win bid!
        self.sendTask(best_bid['team_id'], request_id)
        pass

    def sendTask(self, team_id, request_id):
        '''
        Send task to team_id. Returns True if send was successful. Assumes team_id is valid.
        '''
        # TODO: comment function, test it works.
        try:
            with self.db:
                request  = self.db.query_one('SELECT * FROM requests WHERE request_id = %s', (request_id))
            if request is None:
                lu.writeToLog(self, '[ERROR] Not exist [REQ# {}]'.format(request_id))
                return False
            task_generated = {
                'type': 'task',
                'result': 'win',
                'task': {
                    'request_id': request['request_id'],
                    'k_passengers': request['k_passengers'],
                    'time_requested': request['time_requested'],
                    'time_expected': request['time_expected'],
                    'price_expected': request['price_expected'],
                    'from_port': request['from_port'],
                    'to_port': request['to_port'],
                }
            }
            return tu.writeToTeam(teams[team_id].protocol, task_generated)
        except Exception as e:
            lu.writeToLog(self, '[ERROR] Failed to send task. Error: ', e)
            return False

    def broadcastRequest(self, request_id):
        # TODO: comment function, test it works.
        try:
            with self.db:
                # TODO: Makse sure we get the correct request which is determined by timestamp.
                request = self.db.query_one('SELECT * FROM requests WHERE request_id = %s', (request_id))
            if request is None:
                raise Exception('[ERROR] Not exist [REQ# {}]'.format(request_id))

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
                tu.writeToTeam(protocol, request_generated)
            callId = reactor.callLater(REQUEST_TIMEOUT, self.bidTimeOut, (request['request_id'],))
            self.requestCallId[request['request_id']] = callId
            with self.db:
                query_result = self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                  ('REQUEST_SENT', request['request_id']))
                if not query_result[0]:
                    raise Exception(query_result[1])
        except Exception as e:
            lu.writeToLog(self, '[ERROR] Failed broadcast requests. Error: ', e)

    def bidTimeOut(self, request_id):
        # TODO: comment function, test it works.
        try:
            self.writeToLog("[BID TIMEOUT] [request_id = {}]".format(request_id))
            with self.db:
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;', ('BID_COMPLETED', request_id))
            self.collectBid(request_id)
        except Exception as e:
            lu.writeToLog(self, '[ERROR] Failed to update bid after timeout. Error: ', e)

    def selectBestBid(self, request_id, bids):
        # dummy function now TODO implement
        return bids[0]

    def collectBid(self, request_id):
        # TODO: comment function, test it works.
        # collect bids
        # finds the best bid
        with self.db:
            bids_accepted = self.db.query_list('SELECT * FROM Bids WHERE request_id = %s AND accepted = TRUE;',
                                               (request_id,))

            if len(bids_accepted) == 0:
                # no bids accepted
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                  ('BID_COMPLETED_FAIL', request_id))
                lu.writeToLog(self, '[REQUEST FAILED] No accepted bids for [REQ# {}]'.format(request_id))
            else:
                # there exist some bids
                best_bid = self.selectBestBid(request_id, bids_accepted)
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;'
                                  'UPDATE Bids SET succeeded = %s WHERE bid_id = %s;',
                                  ('BID_COMPLETED_SUCCESS', request_id, True, best_bid['bid_id']))

                lu.writeToLog(self, '[REQUEST SUCCEEDED] Accept bids [BID# {}, TEAM# {}, REQ# {}]'
                                .format(best_bid['bid_id'], best_bid['team_id'], request_id))
                self.sendBidResults(best_bid['team_id'], request_id)

    # ---------------------------------------------------------------

    def onReceiveTaskResponse(self, task_response):
        request_id = task_response['request_id']
        team_id = task_response['team_id']

    def onReceiveTaskUpdate(self, task_update):
        # TODO: implement.
        pass

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
            lu.writeToLog(self, "[ERROR ON RECEIVING BID] Key error [request_id = {}]".format(request_id))
            return

        if request['state'] == 'INIT':
            # already time out
            # TODO: send error message
            lu.writeToLog(self,"[ERROR ON RECEIVING BID] Already timeout [TEAM# {}, REQ# {}]" \
                            .format(team_id, request_id))
            return
        if request['state'] == 'REQUEST_SENT' or request['state'] == 'BID_RECEIVED':
            with self.db:
                # store bid into database
                is_exists = self.db.count('Bids', 'request_id = %s AND team_id = %s', (request_id, team_id))
                if is_exists:
                    # TODO: send error message
                    lu.writeToLog(self,'[ERROR ON RECEIVING BID] Bid already exists [TEAM# {1}, REQ# {0}]'
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
                    lu.writeToLog(self,"[RECEIVING ALL BIDS] for [REQ# {}]".format(request_id))
                    self.requestCallId[request_id].cancel()
                    lu.writeToLog(self,"[TIMEOUT CALLBACK CANCELLED] for [REQ# {}]".format(request_id))

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
