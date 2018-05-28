import re
from allVars import *
import team_utils as tu

def matchIntResponse(query, response):
    return re.match('^' + query + '([0-9]+)\s*$', response)

def matchExactString(query, string, response):
    return re.match('^' + query + string + '\s*$', response)

def matchDroneUpdate(response):
    integer = '([0-9]+)'
    decimal = '([0-9]+.?[0-9]*)'
    # DRONE_UPDATE: <drone_id> <latitude> <longitude> <altitude>
    return re.match('^' + DRONE_UPDATE + integer + '\s+' + decimal + '\s+' + decimal + '\s+' + decimal + '\s*$', response)

def stateToString(state):
    string = ''
    for item in state:
        string += ' ' + str(item)
    return string

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
            'msg': 'Missing attribuete: {}'.format(attr)
        })
        if protocol.factory.protocols[protocol] is None:
            protocol.transport.loseConnection()
        return False
    return True

# TODO: implement function to check if json keys match.
