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
