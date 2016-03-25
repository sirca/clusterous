from threading import Thread
import threading

from flask import Flask, abort, request
import json

import environmentrunner

app = Flask(__name__)

@app.route('/v1/environment', methods=['GET', 'POST'])
def environment():
    global runner
    global delete_event
    if request.method == "GET":
        abort(501)
    elif request.method == "POST":
        if runner != None or (isinstance(runner, Thread) and runner.isAlive()):
            # TODO: make this a proper error case
            return 'environment already running\n', 409

        env_data = request.json

        data_valid = environmentrunner.validate_env(env_data)

        if not data_valid:
            # TODO: make this a proper error case
            return 'Invalid data\n', 400

        runner = Thread(target=environmentrunner.launch_environment, args=(env_data, app.logger, delete_event))
        runner.start()
        return 'accepted\n', 202


if __name__ == "__main__":
    runner = None
    delete_event = threading.Event()
    app.run(debug=True)
