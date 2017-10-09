import Crypto.Hash.SHA512 as SHA512
#import secrets
import secrets
import sqlite3
import os
import traceback as tb
from string import hexdigits, printable
import datetime as  dt
import io
import fileinput
#-------------------------------------core functions-----------------------------------

class Login(object):
    '''
    Base class for Users, Staff and Admins
    '''
    def __init__(self, username=None, password=None, **kargs):
        '''
        Retrieves user from database and verifies password.

        Raises Exception if username/passwords are incorrect

        fields:
            username
            hashedpwd
            salt
            pepper
            user_id
        '''
        if kargs:
            self.__dict__.update(kargs)
            self.username = username
            return
        with Connection() as db:
            user = db.fetch('SELECT * FROM login WHERE username = (?)', username)
            if not user:
                raise LookupError('{} not registered'.format(username))
            self.__dict__.update(user)

            if not self.verify_password(password):
               raise ValueError('Incorrect password')

    def verify_password(self, password):
        try:
            return self.hashedpwd == compute_hash(password, self.salt, self.pepper)[0]
        except AttributeError:
            for pepper in hexdigits:
                if self.hashedpwd == compute_hash(password, self.salt, pepper)[0]:
                    self.pepper = pepper
                    return True
            else:
                    return False

    def update_login(self, newpassword=None):
        '''
        Writes Login username and password back to database.

        raises sqlite3.IntegrityError if username is taken
        '''
        if newpassword:
            self.hashedpwd = compute_hash(newpassword, self.salt, self.pepper)[0]
        with Connection() as db:
            db.execute('''
            UPDATE login SET
            username = :username,
            given_name = :given_name,
            family_name = :family_name,
            dob = :dob,
            hashedpwd = :hashedpwd
            WHERE user_id = :user_id
            ''', **self.__dict__)

    def __setattr__(self, name, value):
        if name == 'user_id':
            raise AttributeError('cannot change user_id')
        super().__setattr__(name, value)

    # def test():
    #     print("Hi")


    @classmethod
    def register(cls, username, password):
        '''
        Creates new login in the database.
        returns id of the new user

        raises sqlite3.IntegrityError if username is taken
        '''
        upper_case = {'A', 'B', 'C', 'D','E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}
        numbers = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}

        f = io.open('CommonPws.txt', 'r')
        flag = 0

        if len(password) < 8:
            raise AttributeError('Password is too short')

        if flag == 0:
            if password.lower() == username.lower():
                raise AttributeError('Do not use username as your password')
            else:
                flag = 0
        if flag == 1:
            for letter in password:
                if letter in upper_case:
                    flag = 2
                elif letter in numbers:
                    flag = 2
            if flag is not 2:
               # print(flag)
                raise AttributeError('Password should have at least one upper_case and one number')
        if flag == 2:
            for line in f:
                if password == line:
                    raise AttributeError('Password is too common')
                else:
                    flag = 3

        #test()
        


        with Connection() as db:
            db.execute(
                'INSERT INTO login(username, hashedpwd, salt) VALUES (?, ?, ?)',
                username, *compute_hash(password)
            )
            _id = db.fetch('SELECT user_id FROM login WHERE username = (?)', username)['user_id']
            return _id

    #@classmethod
    #def checkPasswordValid(username, password):
        # upper_case = {'A', 'B', 'C', 'D','E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}
        # numbers = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}

        # f = io.open('CommonPws.txt', 'r')
        # flag = 0
        
        # if flag == 0:
        #     for letter in password:
        #         if (letter in upper_case and letter in numbers):
        #             flag = 1
        #         else:
        #             raise AttributeError('Password should contain at least one upper_case and one number')
        # elif flag == 1:
        #     for line in f:
        #         if password == line:
        #             raise AttributeError('Password is too common')
        #         else:
        #             flag = 2
        # elif flag == 2:
        #     if password == username:
        #         raise AttributeError('Do not use username as your password')
        #     else:
        #         flag = 3

        # return flag
        # print('x')
        # return 0
        



class User(Login):
    def __init__(self, username=None, password=None, **kargs):
        '''
        additional fields:
            medicare_id
        '''
        super().__init__(username, password, **kargs)
        if not kargs:
            with Connection() as db:
                data = db.fetch('SELECT * from users where user_id = (?)', self.user_id)
                if not data:
                    raise LookupError('{} not registered as user' % username)
                else:
                    self.__dict__.update(data)

    def update(self):
        '''
        Stores medicare_id of current user into database
        '''
        super().update_login()
        with Connection() as db:
            db.execute('''
            UPDATE users
            SET medicare_id = :medicare_id
            WHERE user_id = :user_id
            ''', **self.__dict__)

    def get_prescriptions(self):
        '''
        returns a list of prescriptions
        '''
        with Connection() as db:
            pres = db.fetch('SELECT * from prescriptions WHERE user_id = (?)', self.user_id)
        if type(pres) is dict:
            pres = [pres]
        return [Prescription(**info) for info in pres]


    def get_appointments(self):
        '''
        Fetch a list of all appointments belonging to the user.
        '''
        with Connection() as db:
            res = db.fetch('SELECT * from appointments WHERE user_id = (?)', self.user_id)
        if type(res) is dict:
            res = [res]
        return [Appointment(**info) for info in res]

    def get_requests(self):
        '''
        Fetch a list of all requests made by the user.
        '''
        with Connection() as db:
            requests = db.fetch('SELECT * from rebate_requests WHERE user_id = (?)', self.user_id)
        if type(requests) is dict:
            requests = [requests]
        return [RebateRequest(**info) for info in requests]

    def make_request(self, amount, reason, request_date=None):
        '''
        Issues a new rebate request.
        returns request_id
        '''
        with Connection() as db:
            db.execute('''
                INSERT INTO rebate_requests
                (user_id, amount, reason, request_date)
                values (?, ?, ?, COALESCE(?, date('now')))
                ''', self.user_id, amount, reason, request_date)
            _id = db.fetch('SELECT MAX(request_id) as id FROM rebate_requests')['id']
        return _id

    @classmethod
    def register(cls, username, password):
        '''
        Register a new user in the database.
        '''
        user_id = super().register(username, password)
        with Connection() as db:
            db.execute('INSERT INTO users(user_id) VALUES (?)', user_id)
        return user_id

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('SELECT * from users JOIN login USING (user_id)')
        if type(_all) is dict:
            _all = [_all]
        return [User(**info) for info in _all]

    @staticmethod
    def with_id(user_id):
        with Connection() as db:
            data = db.fetch('''
            SELECT * from users
            JOIN login USING (user_id)
            WHERE user_id = (?)
            ''', user_id)
        return User(**data)

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
                raise LookupError('{} not registered as Medical_Professionals' % username)

    def make_appointment(self, user, info, date, time):
        '''
        Add an appointment to a patient's medical record.
        '''
        with Connection() as db:
            db.execute('''
                INSERT INTO appointments
                (user_id, info, date, time, doctor_id)
                VALUES (?, ?, ?, ?, ?)
                ''', user.user_id, info, date, time, self.user_id)
            _id = db.fetch('SELECT MAX(appointment_id) as id FROM appointments')['id']
        return _id


    def prescribe(self, user, medicine, dosage, frequency, time):
        '''
        Prescribe medication to a patient.
        '''
        with Connection() as db:
            db.execute('''
                INSERT INTO prescriptions
                (user_id, medication, dosage,
                frequency, time, prescribed_by)
                VALUES
                (?, ?, ?, ?, ?, ?)
                ''', user.user_id, medicine,
                dosage, frequency, time, self.user_id)
            _id = db.fetch('SELECT MAX(prescription_id) as id FROM prescriptions')['id']
        return _id

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        cls.register_existing(user_id)
        return user_id

    @classmethod
    def register_existing(cls, user_id):
        '''
        Register existing User as a Medical Professional
        '''
        with Connection() as db:
            db.execute('INSERT INTO medical_professionals VALUES (?)', user_id)

    @staticmethod
    def with_id(user_id):
        with Connection() as db:
            data = db.fetch('''
            SELECT * from medical_professionals
            JOIN login USING (user_id)
            JOIN users USING (user_id)
            WHERE user_id = (?)
            ''', user_id)
        return MedicalProfessional(**data)

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('''
            SELECT * from medical_professionals
            JOIN users USING (user_id)
            JOIN login USING (user_id)
            ''')
        if type(_all) is dict:
            _all = [_all]
        return [MedicalProfessional(**info) for info in _all]

class RebateRequest(object):
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
        with Connection() as db:
            _all = db.fetch('SELECT * from rebate_requests')
        if type(_all) is dict:
            _all = [_all]
        return [RebateRequest(**info) for info in _all]

    @staticmethod
    def get_unprocessed():
        with Connection() as db:
            _all = db.fetch('SELECT * from rebate_requests WHERE approved = NULL')
        if type(_all) is dict:
            _all = [_all]
        return [RebateRequest(**info) for info in _all]

class Appointment:
    def __init__(self, **kargs):
        self.__dict__.update(kargs)

    def update(self):
        with Connection() as db:
            db.execute('''
                UPDATE appointments SET
                info = :info,
                date = :date
                time = :time
                WHERE appointment_id = :appointment_id
                ''', **self.__dict__)

    def delete(self):
        with Connection() as db:
            db.execute('DELETE FROM appointments WHERE appointment_id = (?)', self.appointment_id)

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('SELECT * from appointments')
        if type(_all) is dict:
            _all = [_all]
        return [Appointment(**info) for info in _all]

class Prescription:
    def __init__(self, **kargs):
        self.__dict__.update(kargs)

    def update(self):
        with Connection() as db:
            db.execute('''
                UPDATE prescriptions SET
                {0} = :{0}, {1} = :{1},
                {2} = :{2}, {3} = :{3}
                WHERE {4} = :{4}
                '''.format(
                    'medication', 'dosage'
                    'frequency','time',
                    'prescription_id'
                ), **self.__dict__)

    def delete(self):
        with Connection() as db:
            db.execute('''
                DELETE FROM prescriptions 
                WHERE prescription_id = (?)
                ''', self.prescription_id )

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('SELECT * from prescriptions')
        if type(_all) is dict:
            _all = [_all]
        return [Prescription(**info) for info in _all]

class Staff(Login):
    def __init__(self, username=None, password=None, **kargs):
        super().__init__(username, password, **kargs)
        if not kargs:
            with Connection() as db:
                is_valid = db.fetch('SELECT (?) in Staff', self.user_id)
            if not is_valid:
                raise LookupError('{} not registered as Staff' % username)

    def process_requests(self, request, approved):
        request.approved = approved
        request.processed_by = self.user_id
        request.date_processed = dt.date.today().strftime('%y-%m-%d')
        request.update()

    def update(self):
        super().update_login()

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        with Connection() as db:
            db.execute('INSERT INTO Staff VALUES (?)', user_id)
        return user_id

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('SELECT * from Staff')
        if type(_all) is dict:
            _all = [_all]
        return [Staff(**info) for info in _all]

    @staticmethod
    def with_id(user_id):
        with Connection() as db:
            data = db.fetch('''
            SELECT * from staff
            JOIN login USING (user_id)
            WHERE user_id = (?)
            ''', user_id)
        return Staff(**data)

class Admin(Login):
    def __init__(self, username=None, password=None, **kargs):
        super().__init__(username, password, **kargs)
        if not kargs:
            with Connection() as db:
                is_valid = db.fetch('SELECT (?) in Admin', self.user_id)
            if not is_valid:
                raise LookupError('{} not registered as Admin' % username)

    def update(self):
        super().update_login()

    @classmethod
    def register(cls, username, password):
        user_id = super().register(username, password)
        with Connection() as db:
            db.execute('INSERT INTO Admin VALUES (?)', user_id)
        return user_id

    @staticmethod
    def get_all():
        with Connection() as db:
            _all = db.fetch('SELECT * from Admin')
        if type(_all) is dict:
            _all = [_all]
        return [Admin(**info) for info in _all]

    @staticmethod
    def with_id(user_id):
        with Connection() as db:
            data = db.fetch('''
            SELECT * from admin
            JOIN login USING (user_id)
            WHERE user_id = (?)
            ''', user_id)
        return Admin(**data)
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
        if 'detect_types' not in kargs:
            kargs['detect_types'] = sqlite3.PARSE_DECLTYPES
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

sqlite3.register_converter('TIME', lambda s: dt.datetime.strptime(s.decode(),'%H:%M').time())
sqlite3.register_adapter(dt.time, lambda t: t.strftime('%H:%M'))
sqlite3.register_adapter(dt.date, lambda d: d.strftime('%Y-%m-%d'))
database_setup()
