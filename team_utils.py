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


def TASK_UPDATE_MSG(request_id, status, msg):
    return {
        'type': 'task_update',
        'request_id': request_id,
        'status': status,
        'msg': msg
    }
