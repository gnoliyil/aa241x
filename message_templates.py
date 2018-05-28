THANKS_MSG = {
    'type': 'response',
    'result': 'thanks',
    'msg': None
}

PLEASE_LOGIN_MSG = {
    'type': 'response',
    'result': 'error',
    'msg': 'Please login first.'
}

def ERROR_RESPONSE(error):
    return {
        'type': 'response',
        'result': 'error',
        'msg': error
    }

def REQUEST_MSG(request):
    return {
        'type': 'request',
        'request': {
            'request_id': request['request_id'],
            'k_passengers': request['k_passengers'],
            'time_expected': request['time_expected'],
            'price_expected': request['price_expected'],
            'from_port': request['from_port'],
            'to_port': request['to_port'],
        }
    }
