# Clusterous: Easy Cluster Computing with Docker and AWS
Clusterous is a easy-to-use command line tool for cluster computing on AWS. It allows you to create and manage a cluster on AWS and deploy your software in the form of Docker containers. It is aimed at scientists and researchers who want the on-demand compute power that AWS offers, but don't have the necessary time or technical expertise.

Clusterous is currently under active development. While it is currently usable, it should be regarded as pre-release software.

Requires Linux or OS X and Python 2.7.

# Get started
[Start with the Introduction](docs/manual/01_Introduction.md) of the user manual for an overview of Clusterous.

Next, use the [Quick start guide](docs/manual/02_Quick_start.md) to get started using Clusterous.

You can also read the [full user manual](docs/manual/).

# About

Clusterous is being developed by [SIRCA](http://www.sirca.org.au/) as part of the Big Data Knowledge Discovery (BDKD) project funded by [SIEF](http://www.sief.org.au).

We are aiming to release a stable version 1.0 in Q1 2016. Leading up to the stable release we will be focusing on bugs, security, stability and platform support. We will also be adding some features and refining some existing functionality.
    
# Licensing
Clusterous is available under the Apache License (2.0). See the LICENSE.md file.

Copyright NICTA 2015.

# Developer notes
This section is for developers contributing to Clusterous itself.

## Install from source
To check out the Clusterous source and install from source, first create and enter a Python [virtualenv](https://virtualenv.pypa.io/en/latest/). Then:


    git clone https://<username>@github.com/sirca/bdkd_cluster.git
    cd bdkd_cluster
    python setup.py develop

Note that you will have to ensure that Python 2.7 is used.
    
## Verify

To verify that Clusterous is installed, try:

    clusterous --help
    
And you should see Clusterous' help output.
