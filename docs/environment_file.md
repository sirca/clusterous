# A guide to running your application on a Clusterous cluster


This document is a guide to running your Docker-based cluster application on a Clusterous cluster.

## Background knowledge

This guide assumes you are familiar with Docker and have already made your application run in a Docker container in a test environment.

## Introduction

Once you have made your application run inside a Docker container, you need to provide Clusterous a way of deploying it on to the cluster. This is done by means of an environment file that describes how to do so.

An environment file is a special YAML file that provides Clusterous instructions to build the Docker images for your application, copy files to the cluster, run containers correctly, and create an SSH tunnel if necessary.

## Quick example

This heavily annotated example demonstrates what an environment file looks like. It runs a simple 2-part Python application that displays a web page.


  name: basic-python    # environment name

  # This is the main section where you describe the environment
  environment:
    # Copy any necessary folders to the cluster shared storage.
    # The folder name is relative to the location of this environment file
    copy:
      - "launch_scripts/"
    # Build one or more Docker images. If an image of the same name already exists
    # in your private Docker registry, it won't be built.
    # The folder is relative to the location of this environment file.
    image:
      - dockerfile: "image/"   # folder containing Dockerfile
        image_name: "basic-python"
    # Section that describes your application components
    components:
      master:     # A component named "master"
        machine: master       # Run on the machine named "master"
        cpu: auto             # Evenly share CPU with any other components running on this machine
        image: registry:5000/basic-python   # Name of the Docker image to run
        cmd: "/bin/bash /home/data/launch_scripts/launch_master.sh"   # The command to be run in the container
        ports: "31000"        # Expose container port 31000 as 31000 on the host

      engine:   # Component named "engine". These are the "worker" processes
        machine: worker       # Run on machine(s) named "worker"
        depends: master       # Run only after "master" component has been run
        cpu: 0.5              # 0.5 CPU per running instance of this component
        count: auto           # Automatically run as much as possible on all machines of this type
        image: registry:5000/basic-python     # Name of the Docker image to run (same as master in this example)
        cmd: "/bin/bash /home/data/launch_scripts/launch_engine.sh"   # Launch command

    # Once the above environment is running, create an SSH tunnel to one of the
    # components. This is typically used to expose a web UI or a queue on the local
    # machine. This section is optional.
    expose_tunnel:
      # The component to connect to and the ports. In the format:
      # local_port:component_name:source_port
      service: 8888:master:31000
      # An optional message to display to the user once the port is exposed
      message: "To access the master, use this URL:"

### Components

Components are the fundamental building blocks of a Clusterous application. In the above example, there are two components, a "master", and an "engine" with multiple instances.

A more realistic application may typically contain three components: a master component that handles input parameters, a queue component that accepts jobs from the master, and a worker component that takes jobs from the queue and returns results to it. In such a case, the master and queue would both run on the "master" node, and multiple instances of workers would run on the "worker" nodes. Care must be taken to configure the ports such that all components can talk to each other.

### Organising files
When creating an environment file, it may be best to group all necessary files in a simple directory structure for easy management. For example, the above example may be placed like the following:

  basic-python/
  --image/
    --Dockerfile
  --basic_python/
    --launch_master.sh
    --launch_engine.sh
  --basic-python-env.yml      # the environment file itself

Again, it is important to note that paths you specify inside the envirnment file are relative to the location of the environment file itself. Therefore, the above environment file implies that folders are laid out in this way.

### Mapping Ports
The "ports" field supports a few different syntax options for exposing the container's ports on the host. Multiple ports can be specified in the form:

  ports: 31000,31001,31002

The above example will map the three container ports to the same port on the host. If you want to specify a different port number for the container and the host, simply separate them with a colon, in the form host_port:container_port:

  ports: 31000:8000,31001:8001,31002:8002

### CPU, Memory and Count
The "cpu" field is mandatory and is either set to "auto" or an explicit number (decimals are allowed; 0.5 means half a CPU). Note that there are some limitations what you specify as described in the section Component Resources.

The "count" field is optional, defaulting to 1 instance. If specified, the only value currently accepted is "auto", which means Clusterous will create as many instances as possible on the given machine type, ensuring maximum utilisation.

There is currently no way to specify memory -- memory is assigned to each component (or instance) proportionally based, on the CPU.

### Count vs CPU: The limitations
A key feature of Clusterous is that you don't directly specify how many instances of a component you want running. A component either has one running instance (which may run on the same machine as one or more components), or multiple instances, the exact number of which is automatically determined. In a typical application, this would mean that components such as a UI, master and queueing system would have a single instance each, whereas workers would have as many instances as possible given the cluster size.

A consequence of this is that when specifying the "cpu" field or "count" field for a component, there are certain combinations that are not permitted. For example, when running two different component on the same machine (like a UI and a queue), "cpu" for those components must be set to "auto", indicating that the CPU will be evenly divided among components. On the other hand, for a typical "worker" component, "count" will be "auto", and an explicit "cpu" must be specified.
