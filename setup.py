from setuptools import setup, find_packages


extra = {'scripts': ['bin/clusterous']}

setup(name='clusterous',
      version='0.1.0',
      #package_dir={'': '.'},
      packages=['.'],
      install_requires=['pyyaml', 'pytest', 'mock'],
      **extra
      )

