from db import DBHandler
import keys as k
from demand import DemandGenerator
import csv


def loadRequests(handler):
    '''
    Loads requests into DB from demand.csv file
    '''
    with open('./demand/demand.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        with handler:
            handler.query_one('DELETE From Bids;')
            handler.query_one('DELETE From Requests;')
            for row in reader:
                handler.query_one('INSERT INTO Requests(k_passengers,sent_to,expected_price,from_port,to_port,time_requested,state)  \
                                   VALUES (%s,%s,%s,%s,%s,%s,%s);', (row['k_passengers'],0,row['expected_price'],row['from_port'],
                                   row['to_port'],row['datetime'],'WAITING'))

if __name__ == '__main__':
    DemandGenerator(start_delay=10).generate_file(filename='./demand/demand.csv')
    dbh = DBHandler(k.DB_NAME, k.DB_USER, k.DB_PASSWORD)
    loadRequests(dbh)
