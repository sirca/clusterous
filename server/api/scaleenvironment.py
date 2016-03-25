import time

import json
import requests
import marathon

class ScaleEnvironment(object):
    mesos_url = 'http://localhost:5050/master/state.json'
    marathon_url = 'http://localhost:8080'
    def __init__(self):
        self._update_slave_info()

    def _update_slave_info(self, slave_info=None):
        if slave_info:
            self._mesos_slaves = slave_info
        else:
            self._mesos_slaves = self._get_mesos_slave_info()

    def _get_mesos_slave_info(self):
        r = requests.get(RunEnvironment.mesos_url)
        raw =  r.json()
        r.close()

        info = {}
        for s in raw.get('slaves', []):
            name = s['attributes']['name']
            hostname = s['hostname']
            if s['active'] == False:
                 continue

            if name in info:
                info[name].append(hostname)
            else:
                info[name] = [hostname]

        return info

    def _get_changed_slaves(self, latest_slave_info):
        removed = {}

        for group, hosts in latest_slave_info.iteritems():
            original_hosts_set = set(self._mesos_slaves.get(group, {}))
            new_hosts_set = set(hosts)
            removed_list = list(original_hosts_set - new_hosts_set)
            if removed_list:
                removed[group] = removed_list


        added = {}
        for group, hosts in self._mesos_slaves.iteritems():
            new_hosts_set = set(latest_slave_info.get(group, {}))
            original_hosts_set = set(hosts)
            added_list = list(new_hosts_set - original_hosts_set)
            if added_list:
                added[group] = added_list


        return added, removed

    def _get_marathon_apps(self):
        """
        Return Marathon apps grouped by node group
        """
        client = marathon.MarathonClient(RunEnvironment.marathon_url)

        app_info = {}
        for app in client.list_apps():
            if not app.constraints:
                continue
            group = [ c.value  for c in app.constraints if c.field == 'name' and c.operator == 'CLUSTER'][0]
            group_dict = {'app_id': app.id,
                          'instance_count': app.instances
                         }
            if group not in app_info:
                app_info[group] = [group_dict]
            else:
                app_info[group].append(group_dict)

        return app_info

    def scale_all_apps(self):
        latest_slave_info = self._get_mesos_slave_info()

        added, removed = self._get_changed_slaves(latest_slave_info)

        apps = self._get_marathon_apps()

        if not apps:
            print "No apps, nothing to change"
            self._update_slave_info(latest_slave_info)
            return

        if not added and not removed:
            print "Nothing to add or remove"

        client = marathon.MarathonClient(RunEnvironment.marathon_url)
        # for each group, get appropriate app and calculations, scale accordingly
        for group, hosts in added.iteritems():
            for app in apps.get(group, {}):
                instances_per_host = app['instance_count'] / len(self._mesos_slaves[group])
                num_to_add = instances_per_host * len(hosts)
                client.scale_app(app['app_id'], delta = num_to_add, force=True)
                print "scaling up {0} by {1}".format(app['app_id'], num_to_add)


        # for each group, get appropriate app and remove tasks accordingly
        for group, hosts in removed.iteritems():
            for app in apps.get(group, {}):
                for host in hosts:
                    killed = client.kill_tasks(app['app_id'], scale=True, host=host)
                    print "killing all {0} tasks on host {1}".format(app['app_id'], host)
                    if not killed:
                        print "WARNING, no actual tasks killed?!"

        self._update_slave_info(latest_slave_info)
