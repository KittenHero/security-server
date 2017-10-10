import config
from bottle import Bottle

app = Bottle()

def checkPasswordValid(username, password):
    upper_case = {'A', 'B', 'C', 'D','E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'}
    numbers = {'1', '2', '3', '4', '5', '6', '7', '8', '9', '0'}

    f = io.open('CommonPws.txt', 'r')
    flag = 0

    if flag == 0:
        for letter in password:
            pass
    #   if (letter in upper_case and letter in numbers):
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

@app.route('/api/escape_html/<input_str:path>'):
def escape_html(input_str):
    escape = {
        '<':'&lt;',
        '>':'&gt;',
        '&':'&amp;',
        '"':'&quot;',
        "'":'&#39;'
        '\n':'</br>'
    }
    return ''.join(escape[c] for c in input_str else c)

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
