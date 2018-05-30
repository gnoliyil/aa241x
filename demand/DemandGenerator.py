import csv
import random
import datetime

class DemandGenerator():

    def __init__(self, start_delay=15):
        self.max_passengers = 4
        self.ports = [i for i in range(5)]  # TODO: DECIDE HOW MANY PORTS
        self.start_delay = start_delay
        self.start_datetime = self._get_start_datetime()

    def generate_file(self, filename='demand.csv', k_rows=20, interval=20):
        '''
        Generate a csv file for the demand.
        Filename: must end in .csv
        k_rows: number of rows in outputfile, where each row represents one request.
        interval: time interval between requests, in seconds
        '''
        with open(filename, 'w') as csvfile:
            fieldnames = ['datetime', 'from_port', 'to_port', 'k_passengers', 'expected_price']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(k_rows):
                ports = self._get_ports()
                row = {
                    'datetime': self.start_datetime + datetime.timedelta(seconds=i*interval),
                    'from_port': ports[0],
                    'to_port': ports[1],
                    'k_passengers': self._get_pax(),
                    'expected_price': self._get_expected_price()
                }
                writer.writerow(row)

    def _get_pax(self):
        return random.randint(1,4)

    def _get_ports(self):
        return(random.sample(self.ports, 2))

    def _get_start_datetime(self):
        #today = datetime.datetime.today()
        #start_datetime = datetime.datetime(today.year, today.month, today.day, hour=15, minute=0, second=0)
        start_datetime = datetime.datetime.now() + datetime.timedelta(seconds=self.start_delay)
        return start_datetime

    def _get_expected_price(self):
        # TODO: implement with actual prices.
        return 100

def main():
    dg = DemandGenerator()
    dg.generate_file()

if __name__ == '__main__':
    main()
