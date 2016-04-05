# Clusterous: Easy Cluster Computing with Docker and AWS
Clusterous is a easy-to-use command line tool for cluster computing on AWS. It allows you to create and manage a cluster on AWS and deploy your software in the form of Docker containers. It is aimed at scientists and researchers who want the on-demand compute power that AWS offers, but don't have the necessary time or technical expertise.

Requires Linux or OS X and Python 2.7.

# Features
- Scalable cluster via adding and/or removing nodes
- Shared volume accessible to all nodes
- Central logging system available for your applications
- Reusable and redistributable environments
- Customisable architecture (master-salve by default)
- IPython parallel and Apache Spark environments demos provided
- Commands to upload or download your data to and from the cluster
- Secure connections to the clusters via SSH tunnels
- Own virtual private cloud (VPC)
- Private docker registry
- Setup wizard
- ... and many more

# Get started

[Quick start guide](docs/manual/02_Quick_start.md)

You can also read the [full user manual](docs/manual/).

# Contributing

We heartily welcome external contributions to Clusterous.

- Have you found an issue? Feel free to report it using our [Issues page](https://github.com/sirca/clusterous/issues). 
In order to speed up response times, we ask you to provide as much information on how to reproduce the problem as possible. 

- Developing new features or Fixing bugs? Clone this repository, create a branch, do your magic and then submit a [pull request](https://github.com/sirca/clusterous/pulls).


# Authors

Clusterous is being developed by [SIRCA](http://www.sirca.org.au/) team as part of the Big Data Knowledge Discovery (BDKD) project funded by [SIEF](http://www.sief.org.au).
- Benjamin King (Delivery Manager) 
- Balram Ramanathan
- Lolo Fernandez

# Acknowledgements

BDKD project partners whom gave us their support and guidance: 

- [Data61](http://www.csiro.au/en/Research/D61): Stephen Hardy, Lachlan McCallum, Simon O’Callaghan, Daniel Steinberg, Alastair Reid
- [Macquarie University](https://www.mq.edu.au/): Deb Kane, Daniel Falster, Josh Toomey, James Camac
- [The University of Sydney](http://sydney.edu.au/): Dietmar Muller, Simon Williams, Michael Chin

Open source projects:
- [Apache Mesos](http://mesos.apache.org/)
- [Apache Marathon](https://mesosphere.github.io/marathon/)
- [Docker](https://www.docker.com/)
- [Ansible](https://github.com/ansible/ansible)
    
# Licensing
Clusterous is available under the Apache License (2.0). See the [LICENSE](LICENSE.md) file.

Copyright Data61 2016.
