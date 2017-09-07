import Crypto.Hash.SHA512 as SHA512
import secrets
import random
import sqlite3
import os
import traceback as tb
from string import hexdigits, printable

#-------------------------------------core functions-----------------------------------
class Login:
    def __init__(self, username=None, password=None, **kargs):
        if kargs:
            self.__dict__.update(kargs)
            return
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
        if self.pepper != None:
            return self.hashedpwd == compute_hash(password, self.salt, self.pepper)[0]
        for pepper in hexdigits:
            if self.hashedpwd == compute_hash(password, self.salt, pepper)[0]:
                self.pepper = pepper
                return True
        else:
            return False

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


class User(Login):
    def __init__(self, username=None, password=None, **kargs):
        super().__init__(username, password, **kargs)
        if not kargs:
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

    def get_prescriptions(self):
        with Connection() as db:
            pres = db.fetch('SELECT * from prescriptions WHERE user_id = (?)', self.user_id)
        return pres


    def get_history(self):
        with Connection() as db:
            res = db.fetch('SELECT * from medical_history WHERE user_id = (?)', self.user_id)
        if type(res) == dict:
            res = [res]
        return [MedicalHistory(**info) for info in res]

    def get_requests(self):
        with Connection() as db:
            requests = db.fetch('SELECT * from rebate_requests WHERE user_id = (?)', self.user_id)
        if type(requests) == dict:
            requests = [requests]
        return [RebateRequest(**info) for info in requests]

    def make_request(self, amount, reason, request_date=None):
        with Connection() as db:
            db.execute('''
                INSERT INTO rebate_requests
                (user_id, amount, reason, request_date)
                values (?, ?, ?, COALESCE(?, date('now')))
                ''', self.user_id, amount, reason, request_date)
            _id = db.fetch('''
                SELECT MAX(request_id) FROM rebate_requests 
                WHERE user_id = (?)''', self.user_id).popitem()[1]
        return _id

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        with Connection() as db:
            db.execute('INSERT INTO users(user_id) VALUES (?)', user_id)
        return user_id

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('SELECT * from users JOIN login USING (user_id)')
        return [User(**info) for info in _all]

    @staticmethod
    def generate_medicare():
        def random_id():
            return ''.join([str(random.choice(range(9))) for _ in range(10)])
        with Connection() as db:
            med_id = random_id()
            existing = db.fetch('SELECT medicare_id FROM users')
        while med_id in existing:
            med_id = random_id()
        return med_id

    @staticmethod
    def validate_medicare(medicare_id):
        return True

class MedicalProfessional(User):
    def __init__(self, username=None, password=None, **kargs):
        super().__init__(username, password, **kargs)
        if not kargs:
            with Connection() as db:
                is_valid = db.fetch('SELECT (?) in medical_professionals', self.user_id)
            if not is_valid:
                raise Exception('{} not registered as Medical_Professionals' % username)

    def append_record(self, user, summary, details):
        pass

    def prescribe(self, user, medicine, dosage, frequency, time):
        with Connection() as db:
            db.execute('''
                INSERT INTO prescriptions
                (user_id, medication, dosage,
                frequency, time, prescribed_by)
                VALUES
                (?, ?, ?, ?, ?, ?)
                ''', user.user_id, medicine,
                dosage, frequency, time, self.user_id)
            _id = db.fetch('''
                SELECT MAX(prescription_id) 
                FROM prescriptions 
                WHERE prescribed_by = (?)
                ''', self.user_id).popitem()[1]
        return _id

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        cls.register_existing(user_id)

    @classmethod
    def register_existing(cls, user_id):
        with Connection() as db:
            db.execute('INSERT INTO medical_professionals VALUES (?)', user_id)


    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('''
            SELECT * from medical_professionals
            JOIN users USING (user_id)
            JOIN login USING (user_id)
            ''')
        return [MedicalProfessional(**info) for info in _all]

class RebateRequest:
    def __init__(self, **kargs):
        self.__dict__.update(kargs)

    def update(self):
        with Connection() as db:
            db.execute('''
                UPDATE rebate_requests SET
                amount = :amount, reason = :reason
                request_date = :request_date,
                approved = :approved,
                processed_by = :processed_by,
                date_processed = :date_processed
                WHERE request_id = :request_id
                ''', **self.__dict__)

    def delete(self):
        with Connection() as db:
            db.execute('DELETE FROM rebate_requests WHERE request_id = (?)', self.request_id)

    @staticmethod
    def get_all():
        pass

class MedicalHistory:
    def __init__(self, **kargs):
        self.__dict__.update(kargs)

    def update(self):
        with Connection() as db:
            db.execute('''
                UPDATE medical_history SET
                summary = :summary,
                details = :details
                WHERE history_id = :history_id
                ''', **self.__dict__)

    def delete(self):
        with Connection() as db:
            db.execute('DELETE FROM medical_history WHERE history_id = (?)', self.history_id)

    @staticmethod
    def get_all():
        pass

class Prescription:
    def __init__(**kargs):
        self.__dict__.update(kargs)

    def update(self):
        pass

    def delete(self):
        pass

    @staticmethod
    def get_all():
        pass

class Staff(Login):
    def __init__(self, **kargs):
        pass

    def process_requests(self, request, approved):
        pass

    @classmethod
    def register(cls):
        pass

    @staticmethod
    def get_all():
        pass

class Admin(Login):
    def __init__(self, **kargs):
        pass

    @classmethod
    def register(cls):
        pass

    @staticmethod
    def get_all():
        pass

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
