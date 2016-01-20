# Copyright (c) Jupyter Development Team.
FROM jupyter/minimal-notebook:4.0

MAINTAINER Jupyter Project <jupyter@googlegroups.com>

# Java
RUN apt-get -y update && \
    apt-get install -y --no-install-recommends openjdk-7-jre-headless && \
    apt-get clean

# Mesos libraries
RUN apt-key adv --keyserver keyserver.ubuntu.com --recv E56151BF && \
    DISTRO=debian && \
    CODENAME=wheezy && \
    echo "deb http://repos.mesosphere.io/${DISTRO} ${CODENAME} main" > /etc/apt/sources.list.d/mesosphere.list && \
    apt-get -y update && \
    apt-get --no-install-recommends -y --force-yes install mesos=0.22.1-1.0.debian78 && \
    apt-get clean

# Spark and Mesos pointers
ENV SPARK_HOME /home/data/spark
ENV PYTHONPATH $SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip
ENV MESOS_NATIVE_LIBRARY /usr/local/lib/libmesos.so

# Install Python 2 packages
RUN conda create -p $CONDA_DIR/envs/python2 python=2.7 --yes \
    && conda clean -yt
