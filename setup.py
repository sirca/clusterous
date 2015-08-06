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
      install_requires=['pyyaml', 'pytest', 'mock', 'paramiko',
                        'boto', 'ansible', 'requests', 'marathon', 'sshtunnel',
                        'python-dateutil'],
      **extra
      )
