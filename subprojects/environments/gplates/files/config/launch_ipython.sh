#!/bin/bash
source /home/data/files/config/pre-install.sh
jupyter notebook --no-browser --port 8887 --ip=* --notebook-dir=/home/data/files/notebooks
