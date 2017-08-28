from bottle import route, redirect, request, response
from bottle import run
from bottle import jinja2_template as template
from bottle import TEMPLATE_PATH

TEMPLATE_PATH[:] = ['templates']

@route('/')
@route('/index')
def index():
    user = request.get_cookie('logged_in')
    if not user:
        return redirect('login')
    else:
        return template('index.html', user=user)

@route('/login', method=['GET', 'POST'])
def login():
    if request.method == 'POST':
        response.set_cookie(
                'logged_in',
                request.forms['user'],
                max_age=600
        )
        return redirect('index')
    else:
        return template('login.html')

@route('/logout')
def logout():
    response.delete_cookie('logged_in')
    return redirect('/index')

if __name__ == '__main__':
    run(host='localhost', port=8080, debug=True)
