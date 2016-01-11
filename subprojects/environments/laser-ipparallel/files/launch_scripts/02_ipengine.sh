source /home/data/files/pre-install.sh

ipengine --file $IPYTHON_PROFILE/security/ipcontroller-engine.json --log-to-file=True --log-level=DEBUG --profile-dir=$IPYTHON_PROFILE
