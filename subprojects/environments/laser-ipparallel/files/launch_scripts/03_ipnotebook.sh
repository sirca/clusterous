source /home/data/files/pre-install.sh

cp /home/data/files/bdkd_datastore.conf /root/.bdkd_datastore.conf

ipython2 notebook --no-browser --port 8888 --ip=* --notebook-dir=$NOTEBOOKS # --profile-dir=$IPYTHON_PROFILE
