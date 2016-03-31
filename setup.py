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

from setuptools import setup, find_packages
from clusterous import __version__


extra = {'scripts': ['bin/clusterous']}

setup(name='clusterous',
      version=__version__,
      packages=['clusterous'],
      description = 'Clusterous is a cluster computing tool to deploy Docker containers on AWS',
      author = 'SIRCA',
      author_email = 'lolo.fernandez@sirca.org.au',
      url = 'https://github.com/sirca/clusterous',
      download_url = 'https://github.com/sirca/clusterous/releases/download/v0.5.0/clusterous-0.5.0.tar.gz',
      keywords = ['clusterous', 'docker', 'aws'],
      classifiers = [],
      package_data={'clusterous': [
                        'scripts/ansible/*.yml',
                        'scripts/ansible/hosts',
                        'scripts/ansible/remote/*',
                        'scripts/*.sh',
                        'scripts/*.yml'
                    ]},
      install_requires=['pyyaml', 'pytest', 'mock', 'paramiko',
                        'boto', 'boto3', 'ansible', 'requests',
                        'marathon', 'sshtunnel', 'python-dateutil',
                        'tabulate', 'netaddr'],
      **extra
      )

