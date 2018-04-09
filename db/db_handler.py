import psycopg2 as pg
from psycopg2.sql import SQL, Identifier
from psycopg2.extras import DictCursor

class DBHandler:

    def __init__(self, db_name, user, password='', host='localhost'):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.cur = self.con = None

    def __enter__(self):
        try:
            self.con = pg.connect(dbname=self.db_name, user=self.user, password=self.password, host=self.host)  # will possibly need to include host = 'localhost'
            self.cur = self.con.cursor(DictCursor)
        except pg.Error as e:
            # Perhaps I shouldn't except this error
            print('Failed to establish connection to the database. ERROR:', e)

    def __exit__(self, *exc):
        self.con.commit() # This saves all changes made during the current context
        self.cur.close()
        self.con.close()

    def cursor_is_active(self):
        if self.cur:
            return not self.cur.closed
        return False

    def create_table(self, table_name, table_template):
        """Creates a table with the specified name and with columns as in the
        variable <table_template>."""
        assert(self.cursor_is_active())
        try:
            self.cur.execute('CREATE TABLE {} {};'.format(table_name, table_template))
            self.con.commit()
        except pg.Error as e:
            print('Table creation failed. Rolling back connection. ERROR:', e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()

    def drop_table(self, table_name):
        """Drops the table with the specified name."""
        assert(self.cursor_is_active())
        try:
            self.cur.execute('DROP TABLE {};'.format(table_name))
            self.con.commit()
        except pg.Error as e:
            print('Failed to drop table. Rolling back connection. ERROR:', e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()

    def query_list(self, query, args=()):
        """Executes a query and returns the output as a list."""
        try:
            self.cur.execute(query, args)
            self.con.commit()
            if self.cur.description:
                return self.cur.fetchall()
        except pg.Error as e:
            print('Query failed. Rolling back connection. ERROR:', e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()

    def insert_values(self, table, values_tuple):
        """Insert values into table.
        values_format must be a the format in which the values are written.
        values_tuple must be a tuple of all values, matching the table type."""
        assert(self.cursor_is_active())

        values_format = ''
        num_values = len(values_tuple)
        for i in range(num_values):
            values_format += '%s'
            if i < num_values - 1: values_format += ', '

        sql = 'INSERT INTO {} VALUES({});'.format(table, values_format)

        try:
            self.cur.execute(sql, values_tuple)
            self.con.commit()
            if self.cur.description:
                return self.cur.fetchall()
        except pg.Error as e:
            print('Failed to insert values into {}. Rolling back connection. ERROR:'.format(table), e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()

    def update_values(self, table, condition, columns, values_tuple):
        """Update values of specified columns in table in all rows that satisfy the query condition.
        values_format must be a the format in which the values are written.
        columns must be a tuple of fields in string
        values_tuple must be a tuple of all values, matching the table type."""
        assert(self.cursor_is_active())

        values_format = ''
        num_values = len(values_tuple)
        for i in range(num_values):
            values_format += '%s'
            if i < num_values - 1: values_format += ', '

        identifiers = [Identifier(i) for i in columns]
        if num_values != 1:
            str_identifiers = ('(' + ', '.join(['{}'] * num_values) + ')')
        else:
            str_identifiers = '{}'

        sql = SQL('UPDATE {} SET {} = {} WHERE {};'.format(table, str_identifiers, values_format, condition)) \
                .format(*identifiers)
        try:
            self.cur.execute(sql, values_tuple)
            self.con.commit()
        except pg.Error as e:
            print('Failed to update values in {}. Rolling back connection. ERROR:'.format(table), e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()
