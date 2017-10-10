import subprocess
import os

def main():
    if os.fork():
        subprocess.call(['python3.6', 'Server.py'])
    elif os.fork():
        subprocess.call(['python3.6', 'Database.py'])
    elif os.fork():
        subprocess.call(['python3.6', 'waf.py'])

if __name__ == '__main__':
    main()
