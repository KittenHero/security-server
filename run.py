import subprocess
import os

def main():
    if os.fork():
        subprocess.call(['python', 'Server.py'])
    elif os.fork():
        subprocess.call(['python', 'Database.py'])
    elif os.fork():
        subprocess.call(['python', 'waf.py'])

if __name__ == '__main__':
    main()
