from db_handler import DBHandler
from psycopg2 import sql
import keys as k
import csv

# TODO: chaneg from query_one to insert_values...

def _loadPorts(handler):
    '''
    Loads port info into DB.
    '''
    with handler:
        handler.query_one('DELETE From Ports;')
        for i in range(5):
            handler.query_one('INSERT INTO Ports(port_id,longitude,latitude,altitude)  \
                               VALUES (%s,%s,%s,%s);', (i, 1,2,3))

def _loadRequestStates(handler):
    '''
    Load possible request states into DB.
    '''
    with handler:
        handler.insert_values('Request_States', ('WAITING', 'Request has not been sent yet.'))
        handler.insert_values('Request_States', ('SENT', 'Request has been sent to teams.'))
        handler.insert_values('Request_States', ('NOT_SENT', 'Server was down when time of request happened.'))
        handler.insert_values('Request_States', ('NOT_ACCEPTED', 'Request has been sent to teams, and timeout is done, and no one sumitted a bid.'))
        handler.insert_values('Request_States', ('ACCEPTED', 'Request has been accepted by at least one team and assigned.'))
        handler.insert_values('Request_States', ('ALL_ACCEPTED', 'Request has been accepted by all teams.'))
        handler.insert_values('Request_States', ('ASSIGNED', 'Request has been assigned to winning team.'))
        handler.insert_values('Request_States', ('DONE', 'Team that was assigned finished the taks successfully'))
        handler.insert_values('Request_States', ('FAILED', 'Team that accepted failed to finish the task'))


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
        handler.query_one('DELETE From Drone_States_History;')
        handler.query_one('DELETE From Requests;')
        handler.query_one('DELETE From Request_States;')
        handler.query_one('DELETE From Drones;')
        handler.query_one('DELETE From Teams;')
        handler.query_one('DELETE From Ports;')
    _loadRequestStates(handler)
    _loadTeams(handler)
    _loadPorts(handler)


if __name__ == '__main__':
    main()
