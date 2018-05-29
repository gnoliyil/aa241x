import json
import log_utils as lu


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
        print(team_id)
        lu.writeToLogToTeam(protocol.factory, json.dumps(message), team_id, verbose)
        protocol.sendString(json.dumps(message).encode())
        return True
    except:
        return False

def processAuthentication(protocol, message):
    '''
    Run all logic for authenticating and 'logging in' a user.
    '''
    # TODO: use hasattrs to confirm message format is correct
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
