FROM registry:5000/gplates-v1

MAINTAINER Lolo Fernandez <lolo.fernandez@sirca.org.au>

RUN pip install functools32; \
    pip install jupyter
RUN pip install matplotlib; \
    pip install numpy
ADD files/basemap-1.0.7.tar.gz /root
RUN cd /root; \
    wget http://pkgs.fedoraproject.org/repo/pkgs/python-basemap-data/basemap-1.0.7.tar.gz/48c0557ced9e2c6e440b28b3caff2de8/basemap-1.0.7.tar.gz;\
    tar zxvf basemap-1.0.7.tar.gz; \
    cd /root/basemap-1.0.7; \
    python setup.py install
