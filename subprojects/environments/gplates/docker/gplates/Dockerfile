# Image for pygplates with nlopt

FROM ubuntu:14.04

RUN apt-get update

# install dependencies for pygplates
RUN apt-get install -y libglew-dev
RUN apt-get install -y python2.7-dev
RUN apt-get install -y libboost-dev libboost-python-dev libboost-thread-dev libboost-program-options-dev libboost-test-dev libboost-system-dev
RUN apt-get install -y libqt4-dev
RUN apt-get install -y libgdal1-dev
RUN apt-get install -y libcgal-dev
RUN apt-get install -y libproj-dev
RUN apt-get install -y libqwt-dev
RUN apt-get install -y libxrender-dev libice-dev libsm-dev libfreetype6-dev libfontconfig1-dev

# install wget to enable the pygplates source code to be downloaded from sourceforge
RUN apt-get install -y wget

# use wget to get the correct pygplates package from sourceforge
RUN wget http://sourceforge.net/projects/gplates/files/pygplates/beta-revision-12/pygplates-ubuntu-trusty_1.5_1_amd64.deb

# use dpkg to install 
RUN dpkg -i pygplates-ubuntu-trusty_1.5_1_amd64.deb

# install all the python and ipython notebook requirements
RUN apt-get install -y gcc python-pip
RUN apt-get install -y python-numpy python-scipy python-matplotlib python-pandas python-sympy python-nose
RUN pip install jupyter
RUN pip install ipyparallel
RUN apt-get install -y python-mpltoolkits.basemap

# Install non-linear optimisation package, with options to import into python
ADD nlopt-2.4.2.tar.bz2 /tmp/
RUN cd /tmp/nlopt-2.4.2; \
    ./configure --enable-shared; \
    make; \ 
    make install; \
    rm -fr /tmp/nlopt-2.4.2

# Set python path to find pygplates and nlopt
RUN export PYTHONPATH=${PYTHONPATH}:/usr/lib
RUN export LD_LIBRARY_PATH=/usr/local/lib

RUN apt-get install -y cmake

# Pygplates Python package
ADD gplates-1.5.0-unixsrc.tar.bz2 /tmp
RUN cd tmp/gplates-1.5.0; \
    cmake . ;\
    make -j4 pygplates; \
    mv bin/pygplates.so /usr/local/lib/python2.7/dist-packages/; \
    rm -fr tmp/gplates-1.5.0
