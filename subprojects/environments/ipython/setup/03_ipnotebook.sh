source /root/anaconda/envs/py27/bin/activate py27
export IPYTHON_PROFILE=/home/data/ipython
export IPYTHON_DATA=/home/data/notebook
cd $IPYTHON_DATA
ipython2 notebook --no-browser --port 8888 --ip=* --profile-dir=$IPYTHON_PROFILE
