import config
from bottle import Bottle
from bottle import request
from string import ascii_uppercase as uc, ascii_lowercase as lc, digits, punctuation as sp

app = Bottle()

@app.route('/api/validate_password', method='POST')
def validate_password():
    username = request.forms['username']
    password = request.forms['password']

    strength = 1 if any(d in password for d in digits) else 0
    strength += 1 if any(c in password for c in uc) else 0
    strength += 1 if any(c in password for c in lc) else 0
    strength += 1 if any(c in password for c in sp) else 0

    pwlen = len(password)
    if strength < 3:
        return 'Password Entropy Too Low'
    if pwlen < 8:
        return 'Password Too Short (must be at least 8)'
    with open('CommonPws.txt') as common:
        if password in common:
            return 'Common password detected'

    if levenshtein_distance(username, password) < min(len(username), pwlen):
        return 'Password too similar to username'

    given = request.forms['given_name']
    fam = request.forms['family_name']
    if levenshtein_distance(given, password) < min(len(given), pwlen) or levenshtein_distance(fam, password) < min(len(fam), pwlen):
        return 'Password too similar to name'
    return 'OK'

def levenshtein_distance(a, b):
    m, n = len(a), len(b)
    partial = [[0]*(m + 1) for _ in range(n + 1)]

    # empty strings
    for i in range(n):
        partial[i][-1] = i
    for j in range(m):
        partial[-1][j] = j

    for i in range(n):
        for j in range(m):
            partial[i][j] = min(
                partial[i - 1][j] + 1, # add a char
                partial[i][j - 1] + 1, # remove a char
                partial[i - 1][j - 1] + (1 if a[j] != b[i] else 0)
            )
    return partial[n - 1][m - 1]

@app.route('/api/escape_html/<input_str:path>')
def escape_html(input_str):
    escape = {
        '<':'&lt;',
        '>':'&gt;',
        '&':'&amp;',
        '"':'&quot;',
        "'":'&#39;',
        '\n':'</br>'
    }
    return ''.join(escape[c] if c in escape else c for c in input_str)

if __name__ == '__main__':
    from argparse import ArgumentParser
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
