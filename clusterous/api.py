from flask import Flask, request
from flask.ext.cors import CORS
import yaml
import flask
import json
import logging
import tempfile
import threading
import os.path

import defaults
import clusterousmain
from helpers import NoWorkingClusterException

flask_app = Flask(__name__)
CORS(flask_app)


environment_message = ''

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


def _set_cluster_info(info):
    """
    Writes information to cluster info file. info is a flat dictionary.
    Existing values are not removed; this method only add/updates values
    Returns True if everything goes well
    """
    cluster_info_file = os.path.expanduser(defaults.cluster_info_file)


    existing = {}
    if os.path.exists(cluster_info_file):
        stream = open(cluster_info_file, 'r')
        existing = yaml.load(stream)

    existing.update(info)

    stream = open(cluster_info_file, 'w')
    stream.write(yaml.dump(existing, default_flow_style=False))

    return True

def _get_cluster_info():
    cluster_info_file = os.path.expanduser(defaults.cluster_info_file)
    if not os.path.isfile(cluster_info_file):
        return None

    f = open(os.path.expanduser(cluster_info_file), 'r')
    cluster_info = yaml.load(f)
    return cluster_info

def cluster_status():
    # Check if our start thread is already running
    matching = _get_threads()
    if matching:
        i = _get_cluster_info()
        m = matching[0]
        d = {
                'clusterName': i.get('starting_cluster_name', i.get('cluster_name', '')),
                'controllerInstanceType': '',
                'sharedVolumeSize': '',
                'environmentType': 'ipython',
                'instanceParameters': {
                    'masterInstanceType': '',
                    'workerInstanceType': '',
                    'instanceCount': ''
                },
                'status': '',
                'isActive': False,
                'statusMessage': ''
            }
        if m.isAlive():
            if m.getName() == 'cluster-creation':
                d['statusMessage'] = 'Starting cluster'
                d['status'] = 'starting'
            elif m.getName() == 'cluster-termination':
                d['statusMessage'] = 'Terminating cluster'
                d['status'] = 'terminating'

            return d


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
                'masterInstanceType': info['instances'].get('master', {}).get('type', ''),
                'workerInstanceType': info['instances'].get('worker', {}).get('type', ''),
                'instanceCount': info['instances'].get('master', {}).get('count', 0) + info['instances'].get('worker', {}).get('count', 0)
    }

    cluster_info = _get_cluster_info()
    status_dict = {
                    'status': 'running',
                    'isActive': True,
                    'clusterName': info['cluster']['name'],
                    "controllerInstanceType": info['instances']['controller']['type'],
                    'sharedVolumeSize': info['volume']['total'][:-1],
                    'environmentType': 'ipython',
                    'uptime': uptime_str,
                    'environmentUrl': cluster_info.get('environment_url', ''),
                    'environmentName': 'ipython',
                    'controllerIP': info['cluster']['controller_ip'],
                    'instanceParameters': params
    }

    return status_dict

def run_start_cluster(profile_dict):
    profile_file = 'temp_profile.yml'
    with open(profile_file, 'w') as f:
        f.write(yaml.dump(profile_dict))
    status, app = _init_clusterous_object()
    success, message = app.start_cluster(profile_file)

    if success and message:
        environent_message = message

def _get_threads():
    return [t for t in threading.enumerate() if t.getName() in ['cluster-creation', 'cluster-termination']]

def start_cluster(in_args):
    # Check if our thread is already running
    matching = _get_threads()
    if matching:
        # Already running
        return False


    try:
        params = {
                'master_instance_type': in_args['instanceParameters']['masterInstanceType'],
                'worker_instance_type': in_args['instanceParameters']['workerInstanceType'],
                'instance_count': in_args['instanceParameters']['instanceCount']
        }
        profile = {
                "cluster_name": in_args['clusterName'],
                'controller_instance_type': in_args.get('controllerInstanceType', 't2.small'),
                'shared_volume_size': in_args.get('sharedVolumeSize', 20),
                'environment_file': 'subprojects/environments/ipython-lite/ipython.yml',
                'parameters': params
        }
    except KeyError as e:
        return False

    _set_cluster_info({'starting_cluster_name': in_args['clusterName']})

    t = threading.Thread(target=run_start_cluster, args=(profile,), name='cluster-creation')
    t.daemon = True
    t.start()
    return True

def run_terminate_cluster():
    status, app = _init_clusterous_object()
    app.terminate_cluster()

def terminate_cluster(cluster_name):
    # Check if any thread is already running
    matching = _get_threads()
    if matching:
        # Already running
        return False

    t = threading.Thread(target=run_terminate_cluster, args=(), name='cluster-termination')
    t.daemon = True
    t.start()
    return True

@flask_app.route('/')
def hello_world():
    return "hello world!"


@flask_app.route('/cluster', methods=['POST', 'GET'])
def cluster():
    if request.method == 'POST':
        d = request.get_json(force=True)
        success = start_cluster(d)
        if success:
            return 'Ok'
        else:
            abort(400)
    elif request.method == 'GET':
        val = [cluster_status()]
        resp = flask.make_response(json.dumps(val))
        resp.mimetype = 'application/json'
        return resp


@flask_app.route('/cluster/<id>', methods=['GET', 'DELETE'])
def cluster_id(id):
    if request.method == 'GET':
        status = cluster_status()
        if status and id == status.get('clusterName', None):
            resp = flask.make_response(json.dumps(status))
            resp.mimetype = 'application/json'
            return resp
        else:
            flask.abort(404)
    elif request.method == 'DELETE':
        terminate_cluster(id)
        return 'Ok'


if __name__ == '__main__':
    _configure_logging()
    flask_app.debug = True
    flask_app.run(port=5005)
