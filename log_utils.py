

def writeToLog(factory, message, verbose=True):
    '''
    Prints message to output and writes message to log.
    '''
    if factory.isRunning:
        if verbose:
            print('[SERVER] ' + message)
            print()
        factory.log.write('[SERVER] ' + message + '\n')

def writeToLogFromTeam(factory, message, team_id, verbose=True):
    '''
    Prints to output and writes to log a message that we received from Team team_id
    '''
    if factory.isRunning:
        if team_id is None:
            if verbose: print('[UNKNOWN TEAM] ' + message)
            factory.log.write('[UNKNOWN TEAM]' + message + '\n')
        else:
            if verbose: print('[TEAM ' + team_id + '] ' + message)
            factory.log.write('[TEAM ' + team_id + '] ' + message + '\n')
        if verbose:
            print()

def writeToLogToTeam(factory, message, team_id, verbose=True):
    '''
    Prints message that server sends to Team team_id, and also writes that to the log.
    '''
    if factory.isRunning:
        if team_id is None:
            if verbose: print('[SERVER TO UNKNOWN TEAM] ' + message)
            factory.log.write('[SERVER TO UNKNOWN TEAM]' + message + '\n')
        else:
            if verbose: print('[SERVER TO TEAM ' + team_id + '] ' + message)
            factory.log.write('[SERVER TO TEAM ' + team_id + '] ' + message + '\n')
        if verbose:
            print()
