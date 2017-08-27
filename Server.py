from bottle import get, run

@get('/')
def index():
    return 'USSR'

if __name__ == '__main__':
    run(host='localhost', port=8080, debug=True)