import csv
import random
import datetime

# from .. import allVars as av

class DemandGenerator():

    def __init__(self):
        # self.max_passengers = av.MAX_PASSENGERS  TODO: Figure out how to import allVars, or work around it to get MAX_PASSENGERS
        self.max_passengers = 4
        # self.ports = [i for i in range(av.NUM_PORTS)]
        self.ports = [i for i in range(5)]  # TODO: same here
        self.start_datetime = self._get_start_datetime()

    def generate_file(self, filename='demand.csv', k_rows=20, interval=10):
        '''
        Generate a csv file for the demand.
        Filename: must end in .csv
        k_rows: number of rows in outputfile, where each row represents one request.
        interval: time interval between requests, in seconds
        '''
        with open(filename, 'w') as csvfile:
            fieldnames = ['datetime', 'from_port', 'to_port', 'pax']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(k_rows):
                ports = self._get_ports()
                row = {
                    'datetime': self.start_datetime + datetime.timedelta(seconds=i*interval),
                    'from_port': ports[0],
                    'to_port': ports[1],
                    'pax': self._get_pax()
                }
                writer.writerow(row)

    def _get_pax(self):
        return random.randint(1,4)

    def _get_ports(self):
        return(random.sample(self.ports, 2))

    def _get_start_datetime(self):
        today = datetime.datetime.today()
        start_datetime = datetime.datetime(today.year, today.month, today.day, hour=15, minute=0, second=0)
        return start_datetime

def main():
    dg = DemandGenerator()
    dg.generate_file()

if __name__ == '__main__':
    main()
