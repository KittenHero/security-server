from bottle import get, post, redirect, error
from bottle import request, response
from bottle import Bottle
from bottle import template
from bottle import TEMPLATE_PATH
from bottle import static_file
import config
import secrets
import requests
from string import printable
from contextlib import suppress
secret = ''.join([secrets.choice(printable) for _ in range(16)])
database = f'http://{config.dbhost}:{config.dbport}/api'
#------------------------------main logic---------------------------
app = Bottle()
@app.route('/')
@app.route('/index')
def index():
    user = request.environ['user']
    # TODO: sanitize output
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

    response.set_cookie(
        'session_id', r.cookies['user_id'],
        max_age=600,
        secret=secret
    )
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
    r = requests.put(f'{database}/user', data=request.forms.dict)
    if r.text == 'OK':
        return redirect('/login')
    else:
        return template('signup_general.html', messages=r.text)

@app.route('/signup_professional', method='POST')
def signup_professional():
    r = requests.put(f'{database}/user', data=request.forms.dict)
    if r.text == 'OK':
        requests.put(f'{database}/med', data=request.forms.dict)
        return redirect('/login')
    else:
        return template('signup_professional.html', messages=r.text)

@app.route('/appointments', method='GET')
def view_appointments():
    user = request.environ['user']
    if not user:
        return redirect('/login')
    appointments = requests.get(f'{database}/appointments/{user["user_id"]}').json()['appointments']
    # TODO: sanitize output
    return template('appointments.html', user=user, app=appointments)

@app.route('/make_appointment', method='GET')
def appointment_form():
    user = request.environ['user']
    if not user or user['type'] != 'medical_professionals':
        return redirect('/index')

    userlist = requests.get(f'{database}/user').json()['all users']
    return template('make_appointment.html', user=user, userlist=userlist)

@app.route('/make_appointment', method='POST')
def make_apointment():
    user = request.environ['user']

    if not user or user['type'] != 'medical_professionals':
        return redirect('/index')

    request.forms.update(request.query)
    r = requests.put(f'{database}/appointments', data=request.forms.dict)
    # TODO: sanitize userlist
    userlist = requests.get(f'{database}/user').json()['all users']
    return template('make_appointment.html', user=user, userlist=userlist, messages=r.text)

@app.route('/logout', method=['GET', 'POST'])
def logout():
    response.delete_cookie('session_id')
    return redirect('/index')

@app.hook('before_request')
def get_user():
    user_id = request.get_cookie('session_id', secret=secret)
    if user_id is not None:
        request.environ['user'] = requests.get(f'{database}/user/{user_id}').json()
    else:
        request.environ['user'] = None

@app.hook('before_request')
def sanitize_forms():
    if 'terms' in request.forms:
        del request.forms['terms']
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
