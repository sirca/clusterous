# Install datastore utils and it's wrapper 
cd /home/data/files/config; \
pip install bdkd-datastore-0.1.6.zip; \
pip install  datastorewrapper-0.1.7.tar.gz; \
easy_install -U distribute; \
pip install matplotlib; \
cp bdkd_datastore.conf /root/.bdkd_datastore.conf
