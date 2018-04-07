
from db_handler import DBHandler

handler = DBHandler('aa241x_test', 'lfvarela')
with handler:
    print(handler.query_list('SELECT * FROM Teams;'))
