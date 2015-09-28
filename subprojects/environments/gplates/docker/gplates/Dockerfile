FROM ubuntu:12.04

MAINTAINER Lolo Fernandez <lolo.fernandez@sirca.org.au>

RUN apt-get update
RUN apt-get install -y wget \
 libboost-program-options1.46.1 \
 libboost-python1.46.1 \
 libc6 \
 libgcc1 \
 libgdal1-1.7.0 \
 libgl1-mesa-glx \
 libglew1.6 \
 libglu1-mesa \
 libgmp10 \
 libproj0 \
 libpython2.7 \
 libqt4-network \
 libqt4-opengl \
 libqt4-svg \
 libqt4-xml \
 libqt4-xmlpatterns \
 libqtcore4 \
 libqtgui4 \
 libqwt6 \
 libstdc++6 \
 gmt

RUN apt-get update
RUN apt-get install -y build-essential \
 cmake \
 libboost-python-dev \
 libboost-test-dev \
 libfontconfig1-dev \
 libgdal-dev \
 libglew-dev \
 libproj-dev \
 libqt4-dev \
 libxrender-dev \
 libxt-dev \
 libgmp3-dev \
 libmpfr-dev \
 libmpfr-doc \
 libmpfr4 \
 libmpfr4-dbg \
 libboost-all-dev \
 libqwt-dev \
 python-dev \
 python-pip \
 python-sphinx \
 python-pyshp \
 qt4-dev-tools \
 qt4-qmake

ADD files/pygplates.so.ori /usr/lib/python2.7/dist-packages/pygplates.so

