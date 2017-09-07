from bottle import route, get, post, redirect, error
from bottle import request, response
from bottle import run
from bottle import jinja2_template as template
from bottle import TEMPLATE_PATH
import Database

#------------------------------main logic---------------------------
@route('/')
@route('/index')
def index():
    user = request.get_cookie('logged_in')
    if not user:
        return redirect('/login')
    else:
        return template('index.html', user=user)

@route('/login', method='GET')
def login_form():
    if request.get_cookie('logged_in'):
        return redirect('/index')
    else:
        return template('login.html')

@route('/login', method='POST')
def login():
    try:
        user = Database.Users(request.forms['user'], request.forms['password'])
    except Exception as e:
        return template('login.html', messages=e)
    response.set_cookie(
        'logged_in',
        user.username,
        max_age=600
    )
    return redirect('/index')

@route('/signup', method='GET')
def signup_forms():
    if request.get_cookie('logged_in'):
        return redirect('/index')
    else: return template('signup.html')

@route('/signup', method='POST')
def signup():
    try:
        Database.Users.register(request.forms['user'], request.forms['password'])
    except Exception as e:
        return template('signup.html', messages=e)
    return redirect('/login')

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
