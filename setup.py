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
      # Workaround because PyPi version of ssh tunnel is currently broken
      # https://github.com/pahaz/sshtunnel/issues/21
      # Remove when fixed version of sshtunnel is released
      dependency_links = ['http://github.com/pahaz/sshtunnel/tarball/master/#egg=sshtunnel-4.0.2'],
      **extra
      )
