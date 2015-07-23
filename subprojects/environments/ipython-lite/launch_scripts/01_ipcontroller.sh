export IPYTHON_PROFILE=/home/data/ipython
export IPYTHON_DIR=/home/data/ipython_dir
ipcontroller --log-to-file=True --log-level=DEBUG --reuse --profile=parallel_python2.7 --profile-dir=$IPYTHON_PROFILE --ipython-dir=$IPYTHON_DIR
