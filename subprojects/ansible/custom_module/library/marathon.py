# Copyright 2015 Nicta
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
from urlparse import urlparse

try:
    import json
except ImportError:
    import simplejson as json

try:
    from requests.exceptions import *
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import marathon
    HAS_MARATHON_CLIENT = True
except ImportError:
    HAS_MARATHON_CLIENT = False

class MarathonManager:

    def __init__(self, module):
        self.module = module
        marathon_url = urlparse(module.params.get('marathon_url'))
        self.client = marathon.MarathonClient(
            servers=marathon_url.geturl(),
            timeout=module.params.get('timeout'))
        self.changed = False
        self.log = []
        self.error_msg = None

    def get_log(self, as_string=True):
        return "".join(self.log) if as_string else self.log

    def has_changed(self):
        return self.changed

    def get_apps(self):
        self.changed = False
        filtered_apps = []
        apps = self.client.list_apps()
        for app in apps:
            filtered_apps.append(str(app).split("::")[1])
        return filtered_apps if filtered_apps else ''

    def delete_app(self):
        app_name=self.module.params.get('app_name')
        apps = self.get_apps()
        if '/'+app_name not in apps:
            results = "App: '{0}' not found.".format(app_name)
        else:
            self.changed = True
            id = self.client.delete_app(app_name, force=True)
            results = "App: '{0}' {1}.".format(app_name, 'Destroyed' if id else 'Not found.')
        return results

    def create_app(self):
        app_name=self.module.params.get('app_name')
        count=self.module.params.get('count')
        mem=self.module.params.get('mem')
        cpus=self.module.params.get('cpus')
        cmd=self.module.params.get('cmd')
        image=self.module.params.get('image')

        apps = self.get_apps()
        if '/'+app_name not in apps:
            # Docker container
            if image:
                # Ports
                port_mappings = []
                ports=self.module.params.get('ports')
                if ports:
                    port_goups=ports.split(",")
                    for i in port_goups:
                        pair={"protocol": "tcp",
                              "hostPort": int(i.split(":")[0]),
                              "containerPort": int(i.split(":")[1])}
                        port_mappings.append(pair)

                # Volumes
                volume_mappings = []
                volumes=self.module.params.get('volumes')
                if volumes:
                    volume_goups=volumes.split(",")
                    for i in volume_goups:
                        pair={"mode": "RW",
                              "containerPath": i.split(":")[0],
                              "hostPath": i.split(":")[1]}
                        volume_mappings.append(pair)

                # Container
                from marathon.models.container import MarathonContainer
                force_pull_image=True
                network="BRIDGE"
                privileged=True
                docker={"image": image,
                        "force_pull_image":force_pull_image,
                        "port_mappings":port_mappings,
                        "network":network,
                        "privileged":privileged}
                container=MarathonContainer(docker=docker,volumes=volume_mappings )

                # Launch app
                app = self.client.create_app(app_name, marathon.models.MarathonApp(cmd=cmd, mem=mem, cpus=cpus,container=container))
                self.changed = True

            else:
                app = self.client.create_app(app_name, marathon.models.MarathonApp(cmd=cmd, mem=mem, cpus=cpus))
                self.changed = True

        instances=self.client.get_app(app_name).instances
        if  instances != count:
            self.changed = True
            self.client.scale_app(app_name, count)

        return app_name+":"+str(count)

def main():
    module = AnsibleModule(
        argument_spec = dict(
            marathon_url       = dict(default='http://localhost:8080'),
            app_name           = dict(default='default.app'),
            count              = dict(default=1, type='int'),
            mem                = dict(default=64, type='int'),
            cpus               = dict(default=0.25, type='float'),
            image              = dict(default=None),
            cmd                = dict(default='sleep 100'),
            ports              = dict(default=None),
            volumes            = dict(default=None),
            state              = dict(default='list-apps', choices=['list-apps', 'present', 'absent']),
            timeout            = dict(default=600, type='int'),
        )
    )
    if not HAS_MARATHON_CLIENT:
        module.fail_json(msg="'marathon' is needed for this module. e.g. pip install marathon")
    if not HAS_REQUESTS:
        module.fail_json(msg="'requests' is needed for this module. e.g. pip install requests")

    try:
        manager = MarathonManager(module)
        state = module.params.get('state')
        failed = False

        if state == "list-apps":
            result = manager.get_apps()

        elif state == "present":
            result = manager.create_app()

        elif state == "absent":
            result = manager.delete_app()

        msg = "Results -> {0}".format(result)
        module.exit_json(failed=failed, changed=manager.has_changed(), msg=msg)

    except RequestException as e:
        module.exit_json(failed=True, changed=manager.has_changed(), msg=repr(e))

# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
