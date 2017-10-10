from bottle import get, post, redirect, error
from bottle import request, response
from bottle import Bottle
from bottle import template
from bottle import TEMPLATE_PATH
from bottle import static_file
import config
import secrets
import requests
import datetime as dt
from string import printable
from contextlib import suppress
from collections import Mapping, Iterable
sessions = {}
database = f'http://{config.dbhost}:{config.dbport}/api'
waf = f'http://{config.wafhost}:{config.wafport}/api'
#------------------------------main logic---------------------------
app = Bottle()
@app.route('/')
@app.route('/index')
def index():
    user = request.environ['user']
    if not user:
        return redirect('/login')
    else:
        return template('index.html', user=user)

@app.route('/login', method='GET')
def login_form():
    if request.environ['user']:
        return redirect('/index')
    else:
        return template('login.html')

@app.route('/login', method='POST')
def login():
    r = requests.post(f'{database}/login', data=request.forms.dict)
    if 'user_id' not in r.cookies:
        return template('login.html', messages=r.text)
    sid = secrets.token_hex(4)
    sessions[sid] = (r.cookies['user_id'], dt.datetime.now() + dt.timedelta(seconds=600))
    response.set_cookie('session_id', sid, max_age=600)
    return redirect('/index')

@app.route('/signup_general', method='GET')
def signup_forms_1():
    if request.environ['user']:
        return redirect('/index')
    else: return template('signup_general.html')

@app.route('/signup_professional', method='GET')
def signup_forms_2():
    if request.environ['user']:
        return redirect('/index')
    else: return template('signup_professional.html')

@app.route('/signup_general', method='POST')
def signup_general():
    r = requests.post(f'{waf}/validate_password', data=request.forms.dict)
    if r.text == 'OK':
        r = requests.put(f'{database}/user', data=request.forms.dict)
        if r.text == 'OK':
            return redirect('/login')

    return template('signup_general.html', messages=r.text)

@app.route('/signup_professional', method='POST')
def signup_professional():
    r = requests.post(f'{waf}/validate_password', data=request.forms.dict)
    if r.text == 'OK':
        r = requests.put(f'{database}/user', data=request.forms.dict)
        if r.text == 'OK':
            requests.put(f'{database}/med', data=request.forms.dict)
            return redirect('/login')

    return template('signup_professional.html', messages=r.text)

@app.route('/appointments', method='GET')
def view_appointments():
    user = request.environ['user']
    if not user:
        return redirect('/login')
    appointments = requests.get(f'{database}/appointments/{user["user_id"]}').json()['appointments']
    escape_html(appointments)
    return template('appointments.html', user=user, app=appointments)

@app.route('/make_appointment', method='GET')
def appointment_form():
    user = request.environ['user']
    if not user or user['type'] != 'medical_professionals':
        return redirect('/index')

    userlist = requests.get(f'{database}/user').json()['all users']
    escape_html(userlist)
    return template('make_appointment.html', user=user, userlist=userlist)

@app.route('/make_appointment', method='POST')
def make_apointment():
    user = request.environ['user']

    if not user or user['type'] != 'medical_professionals':
        return redirect('/index')

    request.forms.update(request.query)
    msg = requests.put(f'{database}/appointments', data=request.forms.dict).text
    userlist = requests.get(f'{database}/user').json()['all users']
    escape_html(userlist)
    return template('make_appointment.html', user=user, userlist=userlist, messages=msg)

@app.route('/prescriptions')
def get_prescriptions():
    user = request.environ['user']
    if not user or user['type'] != 'users':
        return redirect('/login')
    prescriptions = requests.get(f'{database}/prescription/{user["user_id"]}').json()['prescriptions']
    escape_html(prescriptions)
    return template('prescription.html', user=user, pres=prescriptions)

@app.route('/make_prescriptions')
def prescription_forms():
    user = request.environ['user']
    if not user or user['type'] != 'medical_professionals':
        return redirect('/login')
    userlist = requests.get(f'{database}/user').json()['all users']
    escape_html(userlist)
    return template('make_prescription.html', user=user, userlist=userlist)

@app.route('/make_prescriptions', method='POST')
def make_prescription():
    user = request.environ['user']
    if not user or user['type'] != 'medical_professionals':
        return redirect('/login')
    request.forms.update(request.query)
    msg = requests.put(f'{database}/prescription', data=request.forms.dict).text

    userlist = requests.get(f'{database}/user').json()['all users']
    escape_html(userlist)
    return template('make_prescription.html', user=user, userlist=userlist, messages=msg)


@app.route('/logout', method=['GET', 'POST'])
def logout():
    sid = request.get_cookie('session_id')
    if sid in sessions:
        del sessions[sid]
    response.delete_cookie('session_id')
    return redirect('/index')

@app.hook('before_request')
def get_user():
    sid = request.get_cookie('session_id')
    if sid is not None and sid in sessions:
        user_id, limit = sessions[sid]
        if limit < dt.datetime.now():
            request.environ['user'] = None
        else:
            user = requests.get(f'{database}/user/{user_id}').json()
            escape_html(user)
            request.environ['user'] = user
            limit = dt.datetime.now() + dt.timedelta(seconds=600)
            response.set_cookie('session_id', sid, max_age=600)
            sessions[sid] = (user_id, limit)
    else:
        request.environ['user'] = None

@app.hook('before_request')
def sanitize_forms():
    if 'terms' in request.forms:
        del request.forms['terms']

def escape_html(iterable):
    '''
    So this was supposed to prevent XSS
    but bottle simple template engine
    already does this
    '''
    return
    if isinstance(iterable, Mapping):
        for k in iterable:
            v = iterable[k]
            if isinstance(v, str):
                iterable[k] = requests.get(f'{waf}/escape_html/{v}').text
    else:
        for item in iterable:
            escape_html(item)

#-------------------------set up html loading------------------------

TEMPLATE_PATH[:] = ['templates']
@app.route('/img/<picture>')
def serve_pictures(picture):
    return static_file(picture, root='img/')

@app.route('/css/<css>')
def serve_css(css):
    return static_file(css, root='css/')

@app.route('/js/<js>')
def serve_js(js):
    return static_file(js, root='js/')

@app.error(404)
def page_not_found(error):
    return 'Page not found'
#---------------------------------run--------------------------------

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Runs server')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-r', '--reloader', action='store_true', help='Enable reloader')
    parser.add_argument('-p', '--port', type=int, default=config.serverport, help='Server\'s listening port')
    parser.add_argument('--host', default=config.serverhost, help='Server\'s listening IP')
    options = vars(parser.parse_args())
    if config.debug:
        options['debug'] = config.debug
    if config.reload:
        options['reloader'] = config.reload
    app.run(**options)
