import json
import log_utils as lu
import server_utils as su


def logOutTeam(factory, team_id):
    if team_id is not None:
        factory.teams[team_id].logOut()
        lu.writeToLog(factory, 'Team ' + team_id + ' logged out.')

def denyTeam(protocol, reason):
    '''
    Close connection with user for given reason
    '''
    writeToTeam(protocol, {
        'type': 'response',
        'result': 'error',
        'msg': reason
    })
    protocol.transport.loseConnection()

def writeToTeam(protocol, message, verbose=True):
    '''
    Writes to the team assigned to this protocol, and logs the message.
    :param dict message
    '''
    try:
        team_id = protocol.factory.protocols[protocol]
        lu.writeToLogToTeam(protocol.factory, json.dumps(message), team_id, verbose=verbose)
        protocol.sendString(json.dumps(message).encode())
        return True
    except:
        return False

def processAuthentication(protocol, message):
    '''
    Run all logic for authenticating and 'logging in' a user.
    '''
    if not su.hasattrs(protocol, message, ['team_id', 'password']): return
    team_id, password = message["team_id"], message["password"]

    # Unsuccessful authentication
    if team_id not in protocol.factory.teams:
        denyTeam(protocol, 'Team {} not found'.format(team_id))

    elif bool(protocol.factory.teams[team_id].isLoggedIn()):
        denyTeam(protocol, 'Team {} is already logged in.'.format(team_id))

    elif not protocol.factory.teams[team_id].tryLogin(password, protocol):
        denyTeam(protocol, 'Password error.')


    # Successful authentication
    else:
        protocol.factory.protocols[protocol] = team_id
        writeToTeam(protocol, {
            'type': 'response',
            'result': 'success',
            'msg': None
        })


# determine if the port position and drone position are close enough
def closeEnough(port_position, drone_position):
    from math import sin, cos, sqrt, atan2, radians

    # approximate radius of earth in km
    epsilon = 5
    R = 6373.0

    lat1 = radians(port_position['latitude'])
    lon1 = radians(port_position['longitude'])
    lat2 = radians(drone_position['latitude'])
    lon2 = radians(drone_position['longitude'])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c * 1000 # meters
    return distance <= epsilon
