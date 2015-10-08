from flask import Flask, request
import flask
import json
import logging

import clusterousmain
# from helpers import NoWorkingClusterException

flask_app = Flask(__name__)

def _configure_logging(level='INFO'):
    logging_dict = {
                        'version': 1,
                        'disable_existing_loggers': False,
                        'formatters': {
                            'standard': {
                                'format': '%(message)s'
                            },
                        },
                        'handlers': {
                            'default': {
                                'level': level,
                                'class':'logging.StreamHandler',
                            },
                        },
                        'loggers': {
                            '': {
                                'handlers': ['default'],
                                'level': level,
                                'propagate': True
                            },
                        }
                    }

    logging.config.dictConfig(logging_dict)

    # Disable logging for various libraries
    # TODO: is it possible to do this in a simpler way?
    libs = ['boto', 'paramiko', 'requests', 'marathon']
    for l in libs:
        logging.getLogger(l).setLevel(logging.WARNING)

def _init_clusterous_object():
    app = None
    status = True
    try:
        app = clusterousmain.Clusterous()
    except clusterousmain.ConfigError as e:
        print >> sys.stderr, 'Error in Clusterous configuration file', e.filename
        print >> sys.stderr, e
        sys.exit(-1)


    return status, app

def cluster_status():
    success, app = _init_clusterous_object()

    if not success:
        return None


    try:
        success, info = app.cluster_status()
    except NoWorkingClusterException as e:
        success, info = False, str(e)

    if not success:
        return None

    uptime_str = ''
    up_time = info['cluster']['up_time']
    if up_time.years > 0: uptime_str += ' {0} years'.format(up_time.years)
    if up_time.months > 0: uptime_str += ' {0} months'.format(up_time.months)
    if up_time.days > 0: uptime_str += ' {0} days'.format(up_time.days)
    if up_time.hours > 0: uptime_str += ' {0} hours'.format(up_time.hours)
    if up_time.minutes > 0: uptime_str += ' {0} minutes'.format(up_time.minutes)


    params = {
                'masterInstanceType': info['instances']['master']['count'],
                'workerInstanceType': info['instances']['worker']['count'],
                'instanceCount': info['instances']['master']['count'] + info['instances']['worker']['count']
    }

    status_dict = {
                    "status": "running",
                    "clusterName": info['cluster']['name'],
                    "controllerInstanceType": info['instances']['controller']['type'],
                    'sharedVolumeSize': info['volume']['total'][:-1],
                    'environmentType': 'ipython',
                    'uptime': uptime_str,
                    'controllerIP': info['cluster']['controller_ip'],
                    'instanceParameters': params
    }

    return status_dict


@flask_app.route('/')
def hello_world():
    return "hello world!"


@flask_app.route('/cluster', methods=['POST', 'GET'])
def cluster():
    if request.method == 'POST':
        return "data: " + str(request.get_json(force=True))
    elif request.method == 'GET':
        val = [cluster_status()]
        resp = flask.make_response(json.dumps(val))
        resp.mimetype = 'application/json'
        return resp


@flask_app.route('/cluster/<id>', methods=['GET'])
def cluster_id(id):
    status = cluster_status()
    if id == status['clusterName']:
        resp = flask.make_response(json.dumps(status))
        resp.mimetype = 'application/json'
        return resp
    else:
        flask.abort(404)

if __name__ == '__main__':
    _configure_logging()
    flask_app.debug = True
    flask_app.run()
