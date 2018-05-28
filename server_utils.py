import team_utils as tu

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
        tu.writeToTeam(protocol, {
            'type': 'response',
            'result': 'error',
            'msg': 'Missing attribute: {}'.format(attr)
        })
        if protocol.factory.protocols[protocol] is None:
            protocol.transport.loseConnection()
        return False
    return True

def getNextRequest(db):
    '''
    Retrieve from DB request that has earliest time_requested and has state WAITING.
    Returns that request or None.
    '''
    with db:
        return db.query_one('SELECT *                                  \
                                   FROM Requests                       \
                                   WHERE time_requested =              \
                                      (SELECT MIN(time_requested)      \
                                       FROM Requests                   \
                                       WHERE state = %s);', ('WAITING',))
