import re
from allVars import *

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
