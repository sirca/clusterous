# Introduction

Clusterous is a tool for cluster computing on [AWS](https://aws.amazon.com). It lets you quickly and easily spin up a cluster of virtual machines on your AWS account and then deploy your parallel application in the form of [Docker](https://www.docker.com/what-docker) containers.

The target users for Clusterous are scientists, data scientists and anyone else who needs on-demand access to powerful parallel computing resources for running their code. As such, it is designed to be easy to use for people who aren't system administrators or cloud computing experts. By simplifying many of the technical aspects of cloud computing, Clusterous lets you focus more on your algorithms and results, and less on APIs, networking and configuration.


## Overview of operation

Clusterous takes the form of a command-line tool, and is currently supported on Linux and Mac OS X (the clusters themselves run Linux). After installing Clusterous and configuring it with your AWS account credentials, you run the command to create a cluster, which is depicted in the following diagram.

![Clusterous Default Cluster Diagram](images/Clusterous_Architecture.png)

Once the cluster is created, you can have your application deployed. Clusterous uses Docker to deploy and run applications, allowing you to avoid all the compatibility and dependency headaches one would typically face when deploying code to another machine.

To run your application, first put it in a Docker container (or multiple containers where necessary) and test it on your local machine. Once you have everything ready, you give Clusterous your Docker image(s) along with information such as the launch commands, the number of CPU cores to use, etc.

All of this is achieved through Clusterous' powerful environment files feature. An environment file is a YAML script that gives Clusterous all the information it needs to prepare your application's environment. Apart from your application parameters, it can copy files to the cluster (useful for configuration) and create an SSH tunnel from the cluster to your own machine, allowing you to easily and securely access your application.

## What Clusterous is not
It's worth covering what Clusterous does not aim to achieve. 

Clusterous is:

* **not** a parallel computing framework. Clusterous takes care of the complex and tedious job of launching and configuring a compute cluster on the cloud and running your code on it. However, it does not provide a solution for adapting your code to run in parallel, nor does it include things such as job queues or load balancing algorithms. There are plenty of existing parallel computing libraries and frameworks for those tasks, and Clusterous aims to run any of them. Each user has different preferences or requirements for parallel computing software - rather than mandate any particular ones, our focus is on simplifying the provisioning of infrastructure and providing a platform.

* **not** a general purpose cloud computing solution. Rather, Clusterous' focus is on on-demand compute clusters for scientists and researchers. While a Clusterous cluster could, with a bit of tweaking, be converted into a public facing web service, that is not the intended use case. There are plenty of other infrastructure tools and libraries that are more suitable for running and managing a resilient, reliable and production-grade website.


## Overview of other features

**Shared volume**: Every cluster has a data volume accessible to all nodes via NFS. The shared volume can be used for storing application configuration, parameters, results, etc.

**Scalable clusters**: Once launched, you can easily add and remove workers from your cluster. Your application will automatically scale to use the available resources.

**Reusable, redistributable environments**: To run your Docker-based application on Clusterous for the first time, create an environment file. The environment file can then be reused as many times as necessary. They can also be shared, allowing others to easily spin up their own cluster running your code.

**Logging system**: Clusters can optionally have a central logging system accessible via a web-based interface. The logging system can be used for debugging and diagnosing problems.

**Multiple configurations**: If you run on multiple AWS regions or use multiple accounts, you can easily manage and switch between configuration profiles.


## Background reading
Before getting started with Clusterous, you need to be familiar with the basics of [AWS](https://aws.amazon.com) and with [Docker](https://www.docker.com/what-docker). In the case of AWS, Clusterous uses the [EC2](https://aws.amazon.com/ec2/) service to run the virtual machines. Read up on concepts such as AWS Regions and the different EC2 instance types. When creating a cluster, you will chose what types of EC2 instances you will use.

Since Clusterous uses Docker to run your application, you need to be able to create and run your own Docker containers and images. If you are new to Docker, start with installing and using Docker on your machine (there are step-by-step guides [for Linux](https://docs.docker.com/linux/) and [OS X](https://docs.docker.com/mac/)).


## About
Clusterous is developed by [SIRCA](http://www.sirca.org.au) as part of the Big Data Knowledge Discovery (BDKD) project funded by [SIEF](http://www.sief.org.au/).

It is written in Python 2.7 and is open source under the Apache 2 license. Full source code is available [on GitHub](https://github.com/sirca/clusterous).
