from db_handler import DBHandler
from psycopg2 import sql


def main():
    handler = DBHandler('aa241x_test', 'lfvarela')
    with handler:
        handler.insert_values('Teams', ('Team 2', True, 't2_password'))
        print(handler.query_list('SELECT * FROM Teams;'))
        handler.insert_values('Bids', ('bid_1', 4.56, False))
        handler.insert_values('Bids', ('bid_2', 7.89, False))
        print(handler.query_list('SELECT * FROM Bids;'))
        handler.update_values('Bids', "bid_id = 'bid_2'", ("price", ), ('1.23', ))
        print(handler.query_list('SELECT * FROM Bids;'))

if __name__ == '__main__':
    main()
