import time


class Simulator():
    def __init__(self, droneStates, drone_id):
        '''
        Simulator of a Drone data sender. Teams should implement their own
        data sender which takes a droneStates queue and appends drone states to it.
        Initialize variables:
            duration: duration of simulation in seconds.
            droneStates: queue of states to which we will add new states received from drone.
        '''
        self.drone_id = drone_id
        self.duration = 20  # Duration in seconds
        self.droneStates = droneStates

    def run(self, run_event):
        '''
        Run the simulator.
        '''
        x = 0.1
        y = 0.2
        z = 0.3
        for _ in range(self.duration):

            # Check if we have to finish thread.
            if not run_event.is_set():
                return

            # NOTE: Use a similar function for when you are using real drones. Simply append the states to
            # the queue, and team server will handle the communication.
            self.droneStates.append({
                'drone_id': self.drone_id,
                'type'    : 'physical',
                'longitude': x,
                'latitude': y,
                'altitude': z,
                'velocity': [1, 2, 3],
                'k_passengers': 2,
                'battery_left': 97,
                'state': 'working',
                'fulfilling': None,
                'next_port': None
            })
            x += 1
            y += 2
            z += 3
            time.sleep(1)
