import os
from flask import Flask

app = Flask(__name__)
PORT = 999

@app.route('/')
def root():
    return '{0}'.format(os.getpid())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)
