import Crypto.Hash.SHA512 as SHA512
import secrets
import sqlite3
import traceback as tb
from string import hexdigits, printable

#-------------------------------------core functions-----------------------------------

def user_login(username, password):
    with Connection() as db:
        user = db.fetch('SELECT * FROM users WHERE username = (?)', username)
        if not user:
            raise Exception('username does not exists')
        for pepper in hexdigits:
            if user['hashedpwd'] == compute_hash(password, user['salt'], pepper)[0]:
                return user
        else:
            raise Exception('Incorrect password')

def user_register(username, password):
    with Connection() as db:
        db.execute(
            'INSERT INTO users(username, hashedpwd, salt) values (?, ?, ?)',
            username, *compute_hash(password)
        )
    return True

#---------------------------------------helper func----------------------------------------
def compute_hash(password, salt=None, pepper=None):
    if salt is None:
        salt = ''.join([secrets.choice(printable) for _ in range(8 + secrets.randbits(8))])
    if pepper is None:
        pepper = secrets.choice(hexdigits)
    return SHA512.new((salt + password + pepper).encode()).digest(), salt

def database_setup():
    print('Setting up database')
    with Connection() as db:
        print('Creating user table')
        db.execute(
        '''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username VARCHAR(32) UNIQUE,
            hashedpwd BYTE(64) NOT NULL,
            salt VARCHAR(8,16) NOT NULL
        )
        '''
        )

class Connection(sqlite3.Connection):
    def __init__(self, database='database.db', **kargs):
        super().__init__(database, **kargs)
        self.cur = self.cursor()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.cur.close()
        self.close()

    def execute(self, command, *args):
        self.cur.execute(command, args)
    def executemany(self, command, *args):
        self.cur.executemany(command, args)

    def fetch(self, command, *args):
        self.cur.execute(command, args)
        header = [item[0] for item in self.cur.description]
        results = [{field:row[i] for i, field in enumerate(header)}
                              for row in self.cur.fetchall()]
        return results if len(results) != 1 else results[0]

database_setup()
