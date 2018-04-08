
from db_handler import DBHandler

def main():
    handler = DBHandler('aa241x_test', 'lfvarela')
    with handler:
        handler.insert_values('Teams', ('Team 2', True, 't2_password'))
        print(handler.query_list('SELECT * FROM Teams;'))
        handler.insert_values('Bids', ('bid_1', 4.56, False))
        print(handler.query_list('SELECT * FROM Bids;'))


if __name__ == '__main__':
    main()
