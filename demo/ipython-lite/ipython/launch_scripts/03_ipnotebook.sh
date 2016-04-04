export IPYTHON_DATA=/home/data/ipython/notebook

cd $IPYTHON_DATA
ipython2 notebook --no-browser --port 8889 --ip=*
