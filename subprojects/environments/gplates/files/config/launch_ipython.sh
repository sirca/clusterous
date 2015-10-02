#!/bin/bash
source /home/data/files/config/pre-install.sh
ipython notebook --no-browser --port 8888 --ip=* --notebook-dir=/home/data/files/notebooks
