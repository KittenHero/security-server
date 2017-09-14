from bottle import route, get, post, redirect, error
from bottle import request, response
from bottle import run
from bottle import template
from bottle import TEMPLATE_PATH
from bottle import static_file
import Database
import secrets
import sqlite3
from string import printable
secret = ''.join([secrets.choice(printable) for _ in range(16)])
#------------------------------main logic---------------------------
@route('/')
@route('/index')
def index():
    user = request.get_cookie('logged_in', secret=secret)
    if not user:
        return redirect('/login')
    else:
        print(user.hashedpwd)
        return template('index.html', user=user.__dict__)

@route('/login', method='GET')
def login_form():
    if request.get_cookie('logged_in', secret=secret):
        return redirect('/index')
    else:
        return template('login.html')

@route('/login', method='POST')
def login():
    try:
        user = Database.User(request.forms['user'], request.forms['password'])
    except Exception as e:
        return template('login.html', messages=e)
    response.set_cookie(
        'logged_in',
        user,
        max_age=600,
        secret=secret
    )
    return redirect('/index')

@route('/signup_general', method='GET')
def signup_forms_1():
    if request.get_cookie('logged_in', secret=secret):
        return redirect('/index')
    else: return template('signup_general.html')

@route('/signup_professional', method='GET')
def signup_forms_2():
    if request.get_cookie('logged_in', secret=secret):
        return redirect('/index')
    else: return template('signup_professional.html')

@route('/signup_general', method='POST')
def signup_general():
    try:
        uid = Database.User.register(request.forms['user'], request.forms['password'])
    except sqlite3.IntegrityError as e:
        return template('signup_general.html', messages='Username already in use')
    user = Database.User.with_id(uid)
    user.given_name = request.forms['fname']
    user.family_name = request.forms['lname']
    user.dob = request.forms['dob'],
    user.update()
    return redirect('/login')

@route('/signup_professional', method='POST')
def signup_professional():
    try:
        uid = Database.MedicalProfessional.register(request.forms['user'], request.forms['password'])
    except sqlite3.IntegrityError as e:
        return template('signup_professional', messages='Username already in use')
    user = Database.MedicalProfessional.with_id(uid)
    user.given_name = request.forms['fname']
    user.family_name = request.forms['lname']
    user.dob = request.forms['dob'],
    user.update()
    return redirect('/login')

@route('/appointments', method='GET')
def view_appointments():
    user = request.get_cookie('logged_in', secret=secret)
    if not user:
        return redirect('/login')
    else:
        return template('appointments.html', user=user.__dict__)


@route('/logout', method=['GET', 'POST'])
def logout():
    response.delete_cookie('logged_in')
    return redirect('/index')

#-------------------------set up html loading------------------------

TEMPLATE_PATH[:] = ['templates']
@route('/img/<picture>')
def serve_pictures(picture):
    return static_file(picture, root='img/')

@route('/css/<css>')
def serve_css(css):
    return static_file(css, root='css/')

@route('/js/<js>')
def serve_js(js):
    return static_file(js, root='js/')

@error(404)
def page_not_found(error):
    return 'Page not found'
#---------------------------------run--------------------------------

if __name__ == '__main__':
    from argparse import ArgumentParser
    parser = ArgumentParser(description='Runs server')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-r', '--reloader', action='store_true', help='Enable reloader')
    parser.add_argument('-p', '--port', type=int, default=8080, help='Server\'s listening port')
    parser.add_argument('--host', default='localhost', help='Server\'s listening IP')
    run(**vars(parser.parse_args()))
