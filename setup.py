from setuptools import setup, find_packages
from clusterous import __version__


extra = {'scripts': ['bin/clusterous']}

setup(name='clusterous',
      version=__version__,
      packages=['clusterous'],
      package_data={'clusterous': [
                        'scripts/ansible/*.yml',
                        'scripts/ansible/hosts',
                        'scripts/ansible/remote/*'
                    ]},
      install_requires=['pyyaml', 'pytest', 'paramiko>=1.15.2',
                        'boto', 'ansible', 'requests>=2.0', 'marathon>=0.7.1', 'sshtunnel>=0.0.4.4',
                        'python-dateutil>=2.4.1', 'setuptools>=17.1'],
      **extra
      )
