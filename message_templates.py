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
            'expected_price': request['expected_price'],
            'from_port': request['from_port'],
            'to_port': request['to_port'],
        }
    }

def TASK_MSG(task):
    return {
        'type': 'task',
        'task': {
            'request_id': task['request_id'],
            'k_passengers': task['k_passengers'],
            'expected_price': task['expected_price'],
            'from_port': task['from_port'],
            'to_port': task['to_port'],
        }
    }

def WINNING_BID_RESULT(request, bid, time_expected):
    return {
        'type': 'bid_result',
        'result': 'win',
        'request_id': request['request_id'],
        'task': {
           'k_passengers': request['k_passengers'],
           'time_expected': time_expected,
           'price': bid['price'],
           'from_port': request['from_port'],
           'to_port': request['to_port'],
        }
    }

def LOSING_BID_RESULT(request):
    return {
        'type': 'bid_result',
        'result': 'lose',
        'request_id': request['request_id']
    }
