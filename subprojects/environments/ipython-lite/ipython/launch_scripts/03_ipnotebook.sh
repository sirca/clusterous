export IPYTHON_PROFILE=/home/data/ipython/profile
export IPYTHON_DATA=/home/data/ipython/notebook

cd $IPYTHON_DATA
ipython2 notebook --no-browser --port 8888 --ip=* --profile-dir=$IPYTHON_PROFILE
