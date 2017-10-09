import Crypto.Hash.SHA512 as SHA512
import secrets
import config
from bottle import Bottle
from bottle import request, response
import sqlite3
import os
from string import hexdigits, printable
import datetime as  dt

app = Bottle()

@app.route('/api/login', method='POST')
def user_login():
    user = find_login(username=request.forms['user'])
    if not user:
        return 'Invalid Username'
    for pepper in hexdigits:
        if compute_hash(request.forms['password'], user['salt'], pepper)[0] != user['hashedpwd']:
            continue
        response.set_cookie('user_id', str(user['user_id']))
        return 'OK'
    else:
        return 'Incorrect password'

def find_login(*args, **kwargs):
    with Connection() as db:
        return db.fetch(
            'SELECT * FROM login WHERE ' +
            ' '.join(f'{k} = (:{k})' for k in kwargs),
            **kwargs
        )

def user_type(user_id, user_type):
    with Connection() as db:
        return db.fetch(
            f'''
            SELECT * FROM {user_type}
            WHERE user_id = {user_id}
            '''
        )

@app.route('/api/user', method='GET')
def all_users():
    with Connection(detect_types=0) as db:
        _all = db.fetch('SELECT * from users JOIN login USING (user_id)')
    if type(_all) is dict:
        _all = [_all]
    for user in _all:
        del user['hashedpwd'], user['salt']
    return {'all users': _all}

@app.route('/api/user', method='PUT')
def register_user():
    newuser = request.forms
    newuser['hashedpwd'], newuser['salt'] = compute_hash(request.forms['password'])
    del newuser['password']

    with Connection() as db:
        try:
            db.execute(
                f'''
                INSERT INTO login ({", ".join(newuser)})
                VALUES ({", ".join(f":{k}" for k in newuser)});
                ''', **newuser
            )
            db.execute(
                f'''
                INSERT INTO users (user_id)
                SELECT user_id FROM login
                WHERE {" AND ".join(f"{k} = :{k}" for k in newuser)}
                ''', **newuser
            )
            return 'OK'
        except sqlite3.IntegrityError:
            return 'Username already in used'

@app.route('/api/med', method='PUT')
def register_med():
    user = request.forms
    del user['password']

    with Connection() as db:
            db.execute(
                f'''
                INSERT INTO medical_professionals (user_id)
                SELECT user_id FROM login WHERE
                {' AND '.join(f'{k} = :{k}' for k in user)}
                ''', **user
            )
            return 'OK'

@app.route('/api/user/<user_id:int>')
def get_user(user_id):
    user = find_login(user_id=user_id)
    if not user:
        return 'Invalid ID'

    user['dob'] = user['dob'].strftime('%d/%m/%Y')
    del user['hashedpwd'], user['salt']
    for t in ('users', 'medical_professionals', 'staff', 'admin'):
        data = user_type(user_id, t)
        if not data: continue
        user['type'] = t
        user.update(data)

    return user

@app.route('/api/appointments', method='PUT')
def make_appointments():
    data = request.forms
    target = find_login(username=data['target'])
    user = find_login(username=data['u'])
    del data['u'], data['target']
    data['doctor_id'] = user['user_id']
    data['user_id'] = target['user_id']
    if not target:
        return 'Invalid target'
    if not user or not user_type(data['doctor_id'], 'medical_professionals'):
        return 'Invalid request'
    with Connection() as db:
        db.execute(
            f'''
            INSERT INTO appointments
            ({','.join(data)})
            VALUES ({','.join(f':{k}' for k in data)})
            ''', **data
        )
        return 'OK'


@app.route('/api/appointments/<user_id:int>')
def get_appointments(user_id):
    with Connection(detect_types=0) as db:
        res = db.fetch('SELECT * from appointments WHERE user_id = (?)', user_id)
    if type(res) is dict:
        res = [res]
    return {'appointments': res}

def compute_hash(password, salt=None, pepper=None):
    if salt is None:
        salt = ''.join([secrets.choice(printable) for _ in range(8 + secrets.randbelow(9))])
    if pepper is None:
        pepper = secrets.choice(hexdigits)
    return SHA512.new((salt + password + pepper).encode()).digest(), salt

def database_setup():
    with open('ddl.sql') as ddl:
        with Connection(config.dbfile) as db:
            db.cur.executescript(ddl.read())

def reset_database():
    os.remove(config.dbfile)
    database_setup(config.dbfile)

class Connection(sqlite3.Connection):
    def __init__(self, database=config.dbfile, **kargs):
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

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Runs Backend')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-r', '--reloader', action='store_true', help='Enable reloader')
    parser.add_argument('-p', '--port', type=int,
                        default=config.dbport, help='Backend\'s listening port')
    parser.add_argument('--host', default=config.dbhost, help='Backend\'s listening IP')

    options = vars(parser.parse_args())
    if config.debug:
        options['debug'] = config.debug
    if config.reload:
        options['reloader'] = config.reload
    app.run(**options)
