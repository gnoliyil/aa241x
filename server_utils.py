import team_utils as tu
import datetime
import log_utils as lu
import message_templates as mt

def hasattrs(protocol, message, attrs):
    for attr in attrs:
        if not hasattr(protocol, message, attr):
            return False
    return True

def hasattr(protocol, message, attr):
    '''
    Check if message has attribute. If not, then we write to team which attribute they are missing. If the team is unknown, we lose the connection.
    '''
    if attr not in message:
        tu.writeToTeam(protocol, ERROR_RESPONSE('Missing attribute: {}'.format(attr)))
        if protocol.factory.protocols[protocol] is None:
            protocol.transport.loseConnection()
        return False
    return True

def getNextRequest(factory, db):
    '''
    Retrieve from DB request that has earliest time_requested and has state WAITING.
    Returns that request or None.
    '''
    while True:
        with db:
            request =  db.query_one('SELECT *                                  \
                                       FROM Requests                       \
                                       WHERE time_requested =              \
                                          (SELECT MIN(time_requested)      \
                                           FROM Requests                   \
                                           WHERE state = %s);', ('WAITING',))
        if request is None:
            return None

        # Check if the time_requested already passed
        if request['time_requested'] < datetime.datetime.now():
            with db:
                db.query_one('UPDATE Requests SET state = %s WHERE request_id = %s;',
                                  ('NOT_SENT', request['request_id']))
            lu.writeToLog(factory, 'REQ# {} missed. New state: NOT SENT.')

        else:
            return request
