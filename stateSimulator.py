import time


class Simulator():
    def __init__(self, droneStates):
        self.duration = 20  # Duration in seconds
        self.droneStates = droneStates

    def run(self):
        x = 0
        y = 0
        for _ in range(self.duration):
            self.droneStates.append((x, y))
            x += 1
            y += 1
            time.sleep(1)
