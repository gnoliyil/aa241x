import psycopg2 as pg


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
            self.cur = self.con.cursor()
        except pg.Error as e:
            # Perhaps I shouldn't except this error
            print('Failed to establish connection to the database. ERROR:', e)
        # return self
        # uncomment line above to enable using handler in the following manner:
        # with db_handler.Handler(...) as handler:
        # otherwise the handler should be used as follows:
        # handler = db_handler.Handler(...)
        # with handler:

    def __exit__(self, *exc):
        self.con.commit() # This saves all changes made during the current context
        self.cur.close()
        self.con.close()

    def cursor_is_active(self):
        if self.cur:
            return not self.cur.closed
        return False

    def create_table(self, table_name, table_template):
        '''Creates a table with the specified name and with columns as in the
        variable <table_template>.'''
        assert(self.cursor_is_active())
        try:
            self.cur.execute('CREATE TABLE {} {};'.format(table_name, table_template))
            self.con.commit()
        except pg.Error as e:
            print('Table creation failed. Rolling back connection. ERROR:', e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()

    def drop_table(self, table_name):
        '''Drops the table with the specified name.'''
        assert(self.cursor_is_active())
        try:
            self.cur.execute('DROP TABLE {};'.format(table_name))
            self.con.commit()
        except pg.Error as e:
            print('Failed to drop table. Rolling back connection. ERROR:', e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()

    def query_list(self, query):
        '''Executes a query and resturns the output as a list.'''
        try:
            self.cur.execute(query)
            self.con.commit()
            if self.cur.description:
                return self.cur.fetchall()
        except pg.Error as e:
            print('Query failed. Rolling back connection. ERROR:', e)
            # resets cursor, otherwise any future executes will generate an InternalError
            self.con.rollback()
