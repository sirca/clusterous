source /root/anaconda/envs/py27/bin/activate py27
export IPYTHON_PROFILE=/home/data/ipython
ipengine --file /home/data/ipython/security/ipcontroller-engine.json --log-to-file=True --log-level=DEBUG --profile-dir=$IPYTHON_PROFILE
