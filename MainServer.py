from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver, NetstringReceiver
from twisted.internet.endpoints import TCP4ServerEndpoint
from twisted.internet import reactor
from sys import stdout
from Team import Team
from vars import *
import json, datetime, traceback
from db import DBHandler
import team_utils as tu
import log_utils as lu
import message_templates as mt
import attributes as atts
import server_utils as su
import keys as k


# TODO in order:
# Incorporate drone COMMUNICATION
# Make sure we can setup connection with other computer.
# Consider sendind FAILED requests again after all WAITING ones have been sent.
# check if when a team submits a bid, their drone is not being considered for another bid.
# TODO: Deny bids that are trying to fulfilled a drone that has already been assigned or has bidded for another request. 

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
        del self.factory.protocols[self]
        lu.writeToLog(self.factory,
            'Connection lost. There are currently %d open connections.' % (self.factory.numProtocols,))

    def stringReceived(self, line):
        '''
        Called when line/message is received from team. Always check 'type' to decide what to do. Call
        methods from here but implement in MainFactory.
        '''
        try:
            # Get message and log it.
            team_id = self.factory.protocols[self]
            message = line.decode()

            lu.writeToLogFromTeam(self.factory, message, team_id, verbose=True)

            # deserialize message
            message = json.loads(message)

            # Check if message has 'type' attribute
            if not su.hasattr(self, message, 'type'): return

            # Team Authentication
            if message['type'] == 'auth':
                tu.processAuthentication(self,message)
                return

            # Team is trying to send a message without our approval or before logging in.
            elif team_id is None or not self.factory.teams[team_id].isLoggedIn():
                tu.writeToTeam(self, mt.PLEASE_LOGIN_MSG)
                return

            # Team is logged in. We can accept data.
            else:
                # Team is sending drone state information, accept it and store it.
                if message['type'] == 'drone_state':
                    self.updateDroneState(team_id, message)
                    tu.writeToTeam(self, mt.THANKS_MSG, verbose=False)


                # Team want to log out. Log them out.
                elif message['type'] == 'logout':
                    tu.logOutTeam(self.factory, team_id)

                elif message['type'] == 'bid':
                    self.onReceiveBid(team_id, message)

                elif message['type'] == 'task_update':
                    self.factory.onReceiveTaskUpdate(message)

        except Exception as e:
            lu.writeToLog(self.factory, '[ERROR] {}'.format(str(e)), verbose=False)
            print(traceback.format_exc())

    def updateDroneState(self, team_id, message):
        # Make sure message has all needed fields.
        if not su.hasattr(self, message, 'drone_state'): return
        new_drone_state = message['drone_state']
        if not su.hasattrs(self, new_drone_state, atts.DRONE_STATE_ATTRS): return

        # Try to insert state into DB. Write back result to team.
        try:
            success = self.factory.teams[team_id].upateDroneState(new_drone_state['drone_id'], new_drone_state, datetime.datetime.now())
            if success:
                tu.writeToTeam(self, mt.THANKS_MSG, verbose=False)
        except Exception as e:
            tu.writeToTeam(self, mt.ERROR_RESPONSE('DB error. Make sure all fields are correct. Error: {}'.format(str(e)))) # Send error
            print(traceback.format_exc())

    def onReceiveBid(self, team_id, message):
        '''
        Handles bid reception from team. Checks request state, stores it in the database,
        updates request state. If all teams submit a bid for a request, stops timeout.
        Calls function to start sending the relevant task.
        '''

        # Make sure message if formatted properly.
        if not su.hasattr(self, message, 'bid'): return
        bid = message['bid']
        if not su.hasattrs(self, bid, atts.BID_ATTRS): return

        # Get request that corresponds to bid from DB and handle errors.
        request_id = bid['request_id']
        try:
            with self.db:
                result = self.db.query_one('SELECT * FROM requests WHERE request_id = %s', (request_id,))
                if result is not None:
                    request = result
                else:
                    raise Exception('[ERROR ON RECEIVING BID] Key error [request_id = {}]'.format(request_id))

            # Case when bid already timed out
            if request['state'] != 'SENT' and request['state'] != 'ACCEPTED':
                raise Exception("[ERROR ON RECEIVING BID] Already timeout [TEAM# {1}, REQ# {0}]".format(team_id, request_id))


            # Try to put into DB and update request_states
            with self.db:
                bid_exists = self.db.count('Bids', 'request_id = %s AND team_id = %s', (request_id, team_id))
                if bid_exists:
                    raise Exception('[ERROR ON RECEIVING BID] Bid already exists [TEAM# {1}, REQ# {0}]'.format(request_id, team_id))
                else:
                    bid_accepted = True if bid['accepted'] else False
                    self.db.insert_values('Bids',
                                          (DBHandler.DEFAULT, bid['price'], bid['seconds_expected'], bid['drone_id'], bid_accepted, False, team_id, request_id))

                # count number of bids
                n_bids = self.db.count('Bids', 'request_id = %s', (request_id,))
                result = self.db.query_one('SELECT sent_to FROM Requests WHERE request_id = %s', (request_id,))
                if result is not None:
                    n_sent = result[0]
                else:
                    raise Exception('[ERROR ON RECEIVING BID] [TEAM# {1}, REQ# {0}]')
            tu.writeToTeam(self, mt.THANKS_MSG, verbose=False)


            # Check if all teams submitted bids to stop timeout and send results.
            if n_bids == n_sent:
                with self.db:
                    self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s; ',
                                      ('ALL_ACCEPTED', request_id))
                lu.writeToLog(self.factory,"Received ALL bids for REQ# {}, timeout callback canceled.".format(request_id))
                self.factory.requestCallIds[request_id].cancel()
                self.factory.sendBidResults(request_id)
            else:
                with self.db:
                    self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                      ('ACCEPTED', request_id))

        except Exception as e:
                lu.writeToLog(self.factory, str(e))
                tu.writeToTeam(self, mt.ERROR_RESPONSE('Bidding error. Error: {}'.format(str(e))))
                print(traceback.format_exc())

    def onReceiveTaskUpdate(self, message):
        if not su.hasattrs(self, message, atts.TASK_UPDATE_ATTS): return
        status = message['status']
        if status not in attts.POSSIBLE_TASK_STATUSES:
            tu.writeToTeam(self, mt.ERROR_RESPONSE('Invalid status.'))
        else:
            tu.writeToTeam(self, mt.THANKS_MSG)

        with self.factory.db:
            self.factory.db.query_list('UPDATE Requests SET status = %;', (status.upper()))

        if status == 'deny':
            with self.factory.db:
                self.factory.db.query_list('UPDATE Requests SET status = %;', (FAILED))

        if status == 'pickup':
            # TODO: Make sure that it is true that the team's drone is close to the pickup port.
            pass

        if status == 'success':
            # TODO: Make sure that it is true that the team's drone is close to the pickup port.
            pass



class MainFactory(ServerFactory):

    def __init__(self):
        '''
        Initializes variables:
            numProtocols: number of open protocols
            protocols: maps { protocol: team_id }
            teams: maps { team_id: Team object }
            passwords: maps { team_id : password }
            requestCallIds = { request_id : requestCallId }
        '''
        self.db = DBHandler(k.DB_NAME, k.DB_USER, k.DB_PASSWORD)
        self.numProtocols = 0
        self.protocols = {}
        self.requestCallIds = {}
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
        self.log.write('\nStarting new log: ' + str(datetime.datetime.now()) + '\n')
        self.startNextBroadcastTimer()

    def stopFactory(self):
        '''
        Called when factory is shutting down. Set isRunning to false so we can log without errors, and closes opened files.
        '''
        self.isRunning = False
        self.log.write('Stopping factory. \n')
        self.log.close()

    # ----------------REQUEST BROADCASTING------------------------------------#

    def startNextBroadcastTimer(self):
        try:
            # Retrieve request.
            request = su.getNextRequest(self, self.db)

            if request is None:
                lu.writeToLog(self, 'No WAITING requests left.')
                return

            # Start timer (by use of callback)
            time_til_broadcast = (request['time_requested'] - datetime.datetime.now()).seconds
            lu.writeToLog(self, 'Time until next broadcast: {}'.format(time_til_broadcast))
            reactor.callLater(time_til_broadcast, self.broadcastNextRequest, (request))

        except Exception as e:
            lu.writeToLog(self, '[ERROR] Failed at broadcastTimer. Error: {}'.format(str(e)))
            print(traceback.format_exc())

    def broadcastNextRequest(self, request):
        '''
        Query request from DB and set a timer to broadcast the given request at the
        time specified in the request.
        '''
        try:
            # Create request message for broadcast.
            request_msg = mt.REQUEST_MSG(request)

            # Send to all teams that are logged in and set timeout.
            lu.writeToLog(self, 'Brodcasting REQ# {} to Teams: {}'.format(request['request_id'], ','.join([self.protocols[protocol] for protocol in self.protocols])))
            for protocol in self.protocols:
                tu.writeToTeam(protocol, request_msg, verbose=False)

            callId = reactor.callLater(REQUEST_TIMEOUT, self.bidTimeOut, request['request_id'])
            self.requestCallIds[request['request_id']] = callId

            # Update request state to sent.
            with self.db:
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                  ('SENT', request['request_id']))
                sent_to = len(self.protocols)
                self.db.query_one('UPDATE Requests SET sent_to = %s WHERE request_id = %s;',
                                  (sent_to, request['request_id']))

            self.startNextBroadcastTimer()

        except Exception as e:
            lu.writeToLog(self, '[ERROR] Failed broadcast requests. Error: {}'.format(str(e)))
            print(traceback.format_exc())

    def bidTimeOut(self, request_id):
        '''
        Call when bid request times out.
        '''
        try:
            lu.writeToLog(self, "[BID TIMEOUT] [REQ# {}]".format(request_id))
            with self.db:
                # Check if someone accepted. If not, update state.
                result = self.db.query_one('SELECT state FROM Requests WHERE request_id = %s', (request_id,))
                if result is not None:
                    state = result[0]
                else:
                    raise Exception('Failed to query request state.')
                if state == 'SENT':
                    self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;', ('NOT_ACCEPTED', request_id))
                    lu.writeToLog(self, '[Request NOT_ACCEPTED] [REQ# {}]'.format(request_id))
                    return

            # If bid was accepted, collect bids.
            self.sendBidResults(request_id)
        except Exception as e:
            lu.writeToLog(self, '[ERROR] On bid timeout. Error: {}'.format(str(e)))
            print(traceback.format_exc())

    # ----------------BID HANDLING--------------------------------------------#

    def selectBestBid(self, bids):
        # dummy function now TODO implement once we know how to calculate the best bid.
        return bids[0]

    def sendBidResults(self, request_id):
        '''
        Collects bids for REQ# request_id and figures out what is the best bid.
        Then we proceed to send the best bid to the given drone/team.
        If this function is called it means at least one bid was submitted.
        '''
        try:
            # Get bids bid and request from DB.
            with self.db:
                bids_accepted = self.db.query_list('SELECT * FROM Bids WHERE request_id = %s AND accepted = TRUE;',
                                                   (request_id,))
                if bids_accepted is None or len(bids_accepted) == 0:
                    raise('Failure collecting bids.')

                request = self.db.query_one('SELECT * FROM Requests WHERE request_id = %s',(request_id,))
                if request is None:
                    raise('Failure collecting bids.')

            # Send result to winning bid
            best_bid = self.selectBestBid(bids_accepted)
            bid_winning_team = best_bid['team_id']
            now = datetime.datetime.now()
            time_expected = now + datetime.timedelta(seconds=best_bid['seconds_expected'])
            with self.db:
                self.db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;', ('ASSIGNED', request_id))
                self.db.query_one('UPDATE Requests SET time_assigned = %s WHERE request_id = %s;', (now, request_id))
                self.db.query_one('UPDATE Requests SET time_expected = %s WHERE request_id = %s;', (time_expected, request_id))
            tu.writeToTeam(self.teams[bid_winning_team].protocol, mt.WINNING_BID_RESULT(request, best_bid, str(time_expected)))

            # Send result to losing teams
            bid_losing_teams = [bid['team_id'] for bid in bids_accepted if bid['team_id'] != bid_winning_team]
            for blt in bid_losing_teams:
                protocol = self.teams[blt].protocol
                if protocol is not None:
                    tu.writeToTeam(self.teams[blt].protocol, mt.LOSING_BID_RESULT(request))

        except Exception as e:
            lu.writeToLog(self, '[ERROR] On sendBidResults. Error: {}'.format(str(e)))
            print(traceback.format_exc())


# 8007 is the port you want to run under. Choose something >1024
def main():
    endpoint = TCP4ServerEndpoint(reactor, 8007)
    endpoint.listen(MainFactory())
    reactor.run()

if __name__ == '__main__':
    main()
