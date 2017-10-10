import config
from bottle import Bottle
from string import ascii_uppercase as uc, ascii_lowercase as lc, digits, punctuation as sp

app = Bottle()

@app.route('/api/validate_password', method='POST')
def validate_password(username, password):
    strength = 1 if any(d in password for d in digits) else 0
    strength += 1 if any(c in password for c in uc) else 0
    strength += 1 if any(c in password for c in lc) else 0
    strength += 1 if any(c in parse_args for c in sp) else 0

    if strength < 3:
        return 'Password Entropy Too Low'
    if len(password) < 8:
        return 'Password Too Short (must be at least 8)'
    with open('CommonPws.txt') as common:
        if password in common:
            return 'Common password detected'

    return 'OK'
if __name__ == '__main__':
    from arsgparse import ArgumentParser
    parser = ArgumentParser(description='Runs WAF')
    parser.add_argument('-d', '--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('-r', '--reloader', action='store_true', help='Enable reloader')
    parser.add_argument('-p', '--port', type=int,
                        default=config.wafport, help='WAF\'s listening port')
    parser.add_argument('--host', default=config.wafhost, help='WAF\'s listening IP')

    options = vars(parser.parse_args())
    if config.debug:
        options['debug'] = config.debug
    if config.reload:
        options['reloader'] = config.reload
    app.run(**options)
