from setuptools import setup, find_packages


extra = {'scripts': ['bin/clusterous']}

setup(name='clusterous',
      version='0.1.0',
      packages=['clusterous'],
      package_data={'clusterous': [
                        'scripts/ansible/*.yml',
                        'scripts/ansible/hosts',
                        'scripts/ansible/remote/*'
                    ]},
      install_requires=['pyyaml', 'pytest', 'mock', 'paramiko', 'boto', 'ansible'],
      **extra
      )
