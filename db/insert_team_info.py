from db_handler import DBHandler
from psycopg2 import sql
import keys as k
import csv

def _loadPorts(handler):
    '''
    Loads port info into DB.
    '''
    with handler:
        handler.query_one('DELETE From Ports;')
        for i in range(5):
            handler.query_one('INSERT INTO Ports(port_id,longitude,latitude,altitude)  \
                               VALUES (%s,%s,%s,%s);', (i, 1,2,3))

def _loadRequests(handler):
    '''
    Loads requests into DB from demand.csv file
    '''
    with open('../demand/demand.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        with handler:
            for row in reader:
                handler.query_one('INSERT INTO Requests(k_passengers,from_port,to_port,time_requested)  \
                                   VALUES (%s,%s,%s,%s);', (row['k_passengers'],row['from_port'],
                                   row['to_port'],row['datetime']))

def _loadTeams(handler):
    '''
    Loads team info into DB.
    '''
    with handler:
        handler.insert_values('Teams', ('team1', False, 'password1'))
        handler.insert_values('Teams', ('team2', False, 'password2'))
        handler.insert_values('Teams', ('team3', False, 'password3'))
        handler.insert_values('Teams', ('team4', False, 'password4'))

def main():
    handler = DBHandler(k.DB_NAME, k.DB_USER, k.DB_PASSWORD)
    with handler:
        handler.query_one('DELETE From Drones;')
        handler.query_one('DELETE From Teams;')
        handler.query_one('DELETE From Requests;')
        handler.query_one('DELETE From Ports;')
    _loadTeams(handler)
    _loadPorts(handler)
    _loadRequests(handler)



if __name__ == '__main__':
    main()
