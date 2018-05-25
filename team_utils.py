import json


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

def writeToTeam(protocol, message):
    '''
    Writes to the team assigned to this protocol, and logs the message.
    :param dict message
    '''
    team_id = protocol.factory.protocols[protocol]
    protocol.factory.writeToLogToTeam(json.dumps(message), team_id)
    protocol.sendString(json.dumps(message).encode())

def processAuthentication(protocol, message):
    '''
    Run all logic for authenticating and 'logging in' a user.
    '''
    team_id, password = message["team-id"], message["password"]

    # Unsuccessful authentication
    if team_id not in protocol.factory.teams:
        protocol.denyTeam('Team {} not found'.format(team_id))

    elif bool(protocol.factory.teams[team_id].isLoggedIn()):
        protocol.denyTeam('Team ' + team_id + ' is already logged in.')

    elif not protocol.factory.teams[team_id].tryLogin(password, protocol):
        protocol.denyTeam('Password error.')


    # Successful authentication
    else:
        protocol.factory.protocols[protocol] = team_id
        writeToTeam(protocol, {
            'type': 'response',
            'result': 'success'
        })
