import logging
import time
import threading

import requests
import marathon
from marathon.models.container import MarathonContainer
from marathon.models.constraint import MarathonConstraint

import ScaleEnvironment


def validate_env(environment_info):
    return True


def launch_environment(environment_info, logger):
    # start launch_thread
    # print dir(environment_info)
    runner = EnvironmentRunner(logger)
    runner.start(environment_info)


mesos_state_url = 'http://localhost:5050/master/state.json'
marathon_url = 'http://localhost:8080'

class EnvironmentRunner:
    class LaunchError(Exception):
        pass

    def __init__(self, logger, delete_event):
        self._logger = logger
        self._delete_event = delete_event

    def start(self, environment_info):
        cluster_info = self._get_cluster_info()
        print "cluster_info", cluster_info
        resources = self._calculate_resources(environment_info, cluster_info)
        print resources
        success = self._launch_components(environment_info, resources)
        scaler = ScaleEnvironment.ScaleEnvironment()
        while True:
            self._logger.debug('Looping')
            # Check if delete environment message sent, wait up to 10 seconds
            if self._delete_event.wait(10):
                self._logger.info('Received delete event, stopping application')
                self._stop_all_apps()
                break
            time.sleep(10)
            scaler.scale_all_apps()


    def _stop_all_apps(self):
        pass

    def _get_cluster_info(self):
        """
        Queries Mesos API and obtains information about cluster.
        Returns information about all slaves and their resources
        """
        mesos_data = None
        r = requests.get(mesos_state_url)
        mesos_data = r.json()

        # Transform cluster info
        if not 'slaves' in mesos_data:
            raise self.LaunchError('Could not obtain cluster information from Mesos')

        cluster_info = {}

        print mesos_data['slaves']

        for host in mesos_data['slaves']:
            if not 'name' in host['attributes']:
                self._logger.warning('No "name" attribute present for mesos slave: {0}'.format(host))
            if not host['attributes']['name'] in cluster_info:
                cluster_info[host['attributes']['name']] = { 'num_nodes': 1,
                                                            'cpus_per_node': host['resources']['cpus'],
                                                            'mem_per_node': host['resources']['mem']
                                                            }
            else:
                # Increment node count
                cluster_info[host['attributes']['name']]['num_nodes'] += 1

        return cluster_info

    def _calculate_resources(self, spec, cluster_info):
        """
        Given information about the cluster, processes environment file spec and
        calculates exact resources. I.e. where the user has specified an "auto"
        value, it calculates the exact cpu, memory and instance count of each
        application component

        The high level algorithm:

        For each component
            validate machine type
            Register machine type, cpu, mem

        For each machine type
            for each component, look at cpu and mem requirements
            determine exact cpu and mem for each component

        """

        machines = {}
        component_resources = {}

        # Get requested resources for each machine
        for component_name, vals in spec['components'].iteritems():
            # Ensure that machine name user has given is valid in this cluster
            if not vals['machine'] in cluster_info:
                raise self.LaunchError('In component "{0}", machine "{1}" '
                                        'does not match any in cluster'.format(
                                        component_name, vals['machine']))

            # Determine auto type
            auto_type = None
            if vals['cpu'] == 'auto':
                auto_type = 'cpu'
            elif vals['count'] == 'auto':
                auto_type = 'count'
            elif vals['cpu'] == 'auto' and vals['count'] == 'auto':
                # Invalid, cannot have auto cpu and auto count
                raise self.LaunchError('For component "{0}", both cpu and count '
                                        'are "auto", which is an invalid '
                                        'combination'.format(component_name))
            else:
                raise self.LaunchError('For component "{0}", cpu is explicitly set to {1} '
                                        'and count to {2}, which is an invalid combination'.format(
                                        component_name, vals['cpu'], vals['count']))
            # Register requested resources for each machine group
            if vals['machine'] not in machines:
                machines[vals['machine']] = {'auto_type': auto_type, 'components': []}

            # The auto type for all components of a machine must be the same
            # If they are mixed, throw an error
            if auto_type != machines[vals['machine']]['auto_type']:
                raise self.LaunchError('Cannot mix components with automatic '
                                        'CPU and automatic Count running on the '
                                        'same machine: {0}'.format(vals['machine']))


            machines[vals['machine']]['components'].append(  {'name':component_name,
                                                'cpu':vals['cpu'], 'count':vals['count']})
        # Determine exact cpu, memory and instance count for each component
        for machine_name, machine_components in machines.iteritems():
            if machine_components['auto_type'] == 'cpu':
                num_components = float(len(machine_components['components']))
                for c in machine_components['components']:
                    resources = {'cpu': cluster_info[machine_name]['cpus_per_node'] / num_components,
                                 'mem': cluster_info[machine_name]['mem_per_node'] / num_components,
                                 'instances': c['count'],
                                 'machine': machine_name
                                 }
                    component_resources[c['name']] = resources
            elif machine_components['auto_type'] == 'count':
                for c in machine_components['components']:
                    cpus_per_node = cluster_info[machine_name]['cpus_per_node']
                    mem_per_cpu = cluster_info[machine_name]['mem_per_node'] / cpus_per_node

                    if c['cpu'] > cpus_per_node:
                        raise self.LaunchError('Component "{0}" is requesting cpu of {1}, but machine '
                                                'type "{2}" only has cpu of {3}'.format(
                                                c['name'], c['cpu'], machine_name, cpus_per_node))

                    # If say there are 2 nodes of 1 cpu each, and each instance requests
                    # 0.4 cpu, there can only be 4 instances running, because cpu
                    # cannot be split across nodes. This handles such situations:

                    # Given requested cpu, the actual number of instances that will run on each node
                    possible_instances_per_node = int(float(cpus_per_node) / c['cpu'])
                    # Amount of cpu that will actually get used in each node (float)
                    possible_cpu_per_node = float(possible_instances_per_node) * c['cpu']

                    # If there is a major difference between what is available and what
                    # will get used, tell the user
                    if (float(cpus_per_node) - possible_cpu_per_node) > 0.05:
                        self._logger.info('Component "{0}" is requesting cpu of {1}, resulting '
                                          'in resources being underused'.format(
                                          c['name'], c['cpu']))

                    resources = {'cpu': c['cpu'],
                                 'mem': mem_per_cpu * float(c['cpu']),
                                 'instances': int(cluster_info[machine_name]['num_nodes'] * possible_instances_per_node),
                                 'machine': machine_name
                                 }
                    component_resources[c['name']] = resources


        return component_resources

    def _launch_components(self, spec, component_resources):
        """
        Takes processed component resources dictionary and performs final steps,
        prepares Marathon data structures and launches components.
        Returns when all components are in started state

        High level algorithm:

        For each component
            normalise cmd path
            generate ports list
            validate dependency text
            prepare shared volume
            create port mapping object
            prepare constraint

        For each prepared component
            submit to Marathon API

        Wait until all components are in started state
        """
        volume_mapping = [{ 'mode': 'RW',
                            'containerPath': '/home/data',
                            'hostPath': '/home/data'}]
        app_containers = []
        for name, c in spec['components'].iteritems():
            # Create ports mappings
            port_mappings = []

            if c['ports']:
                # TODO: this validation should happen befor this point
                if not isinstance(c['ports'], basestring):
                    raise self.LaunchError('In component "{0}", "ports" must be a '
                                            'string value'.format(name))
                for p in c['ports'].split(','):
                    port = p.strip()
                    pair = port.split(':')
                    container_port = host_port = 0
                    if len(pair) == 2:
                        host_port = int(pair[0])
                        container_port = int(pair[1])
                    elif len(pair) == 1:
                        container_port = host_port = int(pair[0])
                    else:
                        raise self.LaunchError('In "{0}", malformed port '
                                                'value: {1}'.format(name, pair))
                    port_mappings.append({  'containerPort': container_port,
                                            'hostPort': host_port,
                                            'protocol': 'tcp'})


            # Validate and generate dependencies
            dependencies = []
            constraints = []
            if c['depends']:
                for d in c['depends'].split(','):
                    depend_str = d.strip()
                    if not depend_str in spec['components']:
                        raise self.LaunchError('Could not find dependency "{0}" as '
                                                'specified in component "{1}"'.format(depend_str, name))
                    dependencies.append('/{0}'.format(depend_str))

            parameters = []
            central_logging_ip = None#self._cluster.get_central_logging_ip()
            if central_logging_ip:
                parameters.append({ "key": "add-host", "value": 'central-logging:{0}'.format(central_logging_ip) })

            docker = {  'image': c['image'], 'port_mappings': port_mappings,
                        'force_pull_image': True, 'network': c['docker_network'].upper(), 'privileged': True,
                        'parameters': parameters}
            container = MarathonContainer(docker=docker, volumes=volume_mapping)

            if c['machine']:
                constraints = [MarathonConstraint(field='name', operator='CLUSTER', value=c['machine'])]

            app_containers.append({ 'name': name,
                                    'container': container,
                                    'cmd': c['cmd'],
                                    'dependencies': dependencies,
                                    'constraints': constraints})

        # Launch containers

        client = marathon.MarathonClient(servers=marathon_url, timeout=600)
        for container in app_containers:
            # Check if app already exists
            app_list = client.list_apps()
            if container['name'] in [ a.id.strip('/') for a in app_list ]:
                raise self.LaunchError('Found a running component named "{0}". '
                                        'Is an environment is already '
                                        'running?'.format(container['name']))
            res = component_resources[container['name']]

            in_str = 'instance' if res['instances'] == 1 else 'instances'
            self._logger.info('Starting {0} {1} of {2}'.format(res['instances'],
                                in_str, container['name']))

            app = client.create_app(container['name'],
                    marathon.models.MarathonApp(cmd=container['cmd'],
                                                dependencies=container['dependencies'],
                                                mem=res['mem'],
                                                cpus=res['cpu'],
                                                instances=res['instances'],
                                                container=container['container'],
                                                constraints=container['constraints']
                                                ))



        # Wait for applications to start running
        self._logger.debug('Waiting for components to start up...')
        expected_containers = len(app_containers)
        running_containers = []
        start_time = time.time()
        elapsed_time = 0
        while (elapsed_time < 1800 and
               len(running_containers) < expected_containers):
            time.sleep(3)
            for container in app_containers:
                name = container['name']
                if name in running_containers:
                    continue

                app = client.get_app(name)

                # Examine Marathon tasks
                if (app.tasks and
                    len(app.tasks) == component_resources[name]['instances']):
                    all_tasks_running = True
                    # Ensure that all tasks (instances) are running
                    for task in app.tasks:
                        if not task.started_at:
                            # If at least 1 task is not running
                            all_tasks_running = False
                            break
                    if all_tasks_running:
                        running_containers.append(name)

            elapsed_time = time.time() - start_time


        success = True
        launched = ', '.join(running_containers)

        if elapsed_time >= 1800:
            self._logger.warning('Timed out waiting for components to launch')
            self._logger.warning('One or more containers are either have problems '
                                 'or are are taking very long to start')
            success = False

        if len(running_containers) < expected_containers:
            self._logger.warning('Could not launch all components')
            success = False

        self._logger.info('Launched {0} components: {1}'.format(len(running_containers), launched))

        return success
