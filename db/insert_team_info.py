from db_handler import DBHandler
from psycopg2 import sql
import keys as k


def main():
    handler = DBHandler(k.DB_NAME, k.DB_USER, k.DB_PASSWORD)
    with handler:
        handler.insert_values('Teams', ('team1', False, 'password1'))
        handler.insert_values('Teams', ('team2', False, 'password2'))
        handler.insert_values('Teams', ('team3', False, 'password3'))
        handler.insert_values('Teams', ('team4', False, 'password4'))

if __name__ == '__main__':
    main()
