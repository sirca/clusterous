export IPYTHON_PROFILE=/home/data/ipython
export IPYTHON_DIR=/home/data/ipython_dir
ipengine --file /home/data/ipython/security/ipcontroller-engine.json --log-to-file=True --log-level=DEBUG --profile-dir=$IPYTHON_PROFILE --ipython-dir=$IPYTHON_DIR
