import Crypto.Hash.SHA512 as SHA512
import secrets
import random
import sqlite3
import os
import traceback as tb
from string import hexdigits, printable

#-------------------------------------core functions-----------------------------------
class Login:
    def __init__(self, username, password):
        with Connection() as db:
            user = db.fetch('SELECT * FROM login WHERE username = (?)', username)
            if not user:
                raise Exception('{} not registed'.format(username))
            for pepper in hexdigits:
                if user['hashedpwd'] == compute_hash(password, user['salt'], pepper)[0]:
                    self.__dict__.update(user)
                    self.pepper = pepper
                    return
            else:
                raise Exception('Incorrect password')

    def verify_password(self, password):
        return self.hashedpwd == compute_hash(password, self.salt, self.pepper)[0]

    def update_login(self, newpassword):
        self.hashedpwd = compute_hash(newpassword, self.salt, self.pepper)[0]
        with Connection() as db:
            db.execute('''
            UPDATE login SET
            username = :username,
            hashedpwd = :hashedpwd
            WHERE user_id = :user_id
            ''', **self.__dict__)

    @classmethod
    def register(cls, username, password):
        with Connection() as db:
            db.execute(
                'INSERT INTO login(username, hashedpwd, salt) VALUES (?, ?, ?)',
                username, *compute_hash(password)
            )
            return db.fetch('SELECT user_id FROM login WHERE username = (?)', username)['user_id']


class Users(Login):
    def __init__(self, username, password):
        super().__init__(username, password)
        with Connection() as db:
            data = db.fetch('SELECT * from users where user_id = (?)', self.user_id)
            if not data:
                raise Exception('{} not registered as user' % username)
            else:
                self.__dict__.update(data)

    def update_data(self):
        with Connection() as db:
            db.execute('''
            UPDATE users 
            SET medicare_id = :medicare_id
            WHERE user_id = :user_id
            ''', **self.__dict__)

    def get_history(self):
        with Connection() as db:
            return db.fetch('SELECT * from medical_history WHERE user_id = (?)', self.user_id)

    def get_requests(self):
        with Connection() as db:
            return db.fetch('SELECT * from rebate_requests WHERE user_id = (?)', self.user_id)

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        with Connection() as db:
            db.execute('INSERT INTO users(user_id) VALUES (?)', user_id)
        return user_id

    @staticmethod
    def all():
        with Connection() as db:
            return db.fetch('SELECT * from users JOIN login USING (user_id)')

    @staticmethod
    def generate_medicare():
        def random_id():
            return ''.join([str(random.choice(range(9))) for _ in range(10)])
        with Connection() as db:
            med_id = random_id()
            while db.fetch('SELECT (?) in users.medicare_id', med_id):
                med_id = random_id()
            return med_id

    @staticmethod
    def validate_medicare(medicare_id):
        return True

class Medical_Professionals(Users):
    def __init__(self, username, password):
        super().__init__(username, password)
        with Connection() as db:
            is_valid = db.fetch('SELECT (?) in medical_professionals', self.user_id)
            if not is_valid:
                raise Exception('{} not registered as Medical_Professionals' % username)

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        with Connection() as db:
            db.execute('INSERT INTO medical_professionals VALUES (?)', user_id)

    @staticmethod
    def all():
        with Connection() as db:
            return db.fetch('''
            SELECT * from medical_professionals
            JOIN users USING (user_id)
            JOIN login USING (user_id)
            ''')

#---------------------------------------helper func----------------------------------------
def compute_hash(password, salt=None, pepper=None):
    if salt is None:
        salt = ''.join([secrets.choice(printable) for _ in range(8 + secrets.randbelow(9))])
    if pepper is None:
        pepper = secrets.choice(hexdigits)
    return SHA512.new((salt + password + pepper).encode()).digest(), salt

def database_setup(database='database.db'):
    with open('ddl.sql') as ddl:
        with Connection(database) as db:
            db.cur.executescript(ddl.read())

def reset_database(database='database.db'):
    os.remove(database)
    database_setup(database)


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

    def execute(self, command, *args, **kargs):
        if kargs:
            self.cur.execute(command, kargs)
        else:
            self.cur.execute(command, args)
    def executemany(self, command, *args):
        self.cur.executemany(command, args)

    def fetch(self, command, *args, **kargs):
        if kargs:
            self.cur.execute(command, kargs)
        else:
            self.cur.execute(command, args)
        header = [item[0] for item in self.cur.description]
        results = [{field:row[i] for i, field in enumerate(header)}
                              for row in self.cur.fetchall()]
        return results if len(results) != 1 else results[0]

database_setup()
