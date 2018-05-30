DRONE_STATE_ATTRS = [
    'drone_id',
    'longitude',
    'latitude',
    'altitude',
    'velocity',
    'k_passengers',
    'battery_left',
    'state',
    'fulfilling',
    'next_port'
]

BID_ATTRS = [
    'request_id',
    'accepted',
    'drone_id',
    'seconds_expected',
    'price',
]

TASK_UPDATE_ATTS = [
  'request_id',
  'status',         # 'confirm', 'pickup', 'success' or 'failure'
  'msg'
]

POSSIBLE_TASK_STATUSES = {'confirm', 'deny', 'pickup', 'success','failure'}
