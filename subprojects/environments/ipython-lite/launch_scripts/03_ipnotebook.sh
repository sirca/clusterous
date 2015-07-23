export IPYTHON_PROFILE=/home/data/ipython
export IPYTHON_DATA=/home/data/notebook
export IPYTHON_DIR=/home/data/ipython_dir
cd $IPYTHON_DATA
ipython2 notebook --no-browser --port 8888 --ip=* --profile-dir=$IPYTHON_PROFILE --ipython-dir=$IPYTHON_DIR
