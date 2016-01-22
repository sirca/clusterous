# A guide to running your application on a Clusterous cluster


This document is a guide to running your Docker-based cluster application on a Clusterous cluster.

## Background knowledge

This guide assumes you are familiar with Docker and have already made your application run in a Docker container in a test environment.

## Introduction

Once you have made your application run inside a Docker container, you need to provide Clusterous a way of deploying it on to the cluster. This is done by means of an environment file that describes how to do so.

An environment file is a special YAML file that provides Clusterous instructions to build the Docker images for your application, copy files to the cluster, run containers correctly, and create an SSH tunnel if necessary.

## Running the Docker application in Clusterous
There are two things to keep in mind when making your application run correctly in a Clusterous cluster.

- Docker containers in Clusterous can only expose ports in the range 1024-65535 (inclusive). This means that if different parts of your application need to communicate with each other (e.g. the workers talking to the master), or be open to your machine (e.g. if your application has a web interface), the exposed ports must be in the above range. In practice, this is only of concern if any part of your application uses a well-known port (<1024). If so, you must be able to customise your application to only use ports between 1024-65525.
- All Clusterous clusters have a dedicated "shared volume", which is an NFS volume accessible to all nodes. This volume is mounted in /home/data, and is typically used for launch scripts, common configuration files and so on, as well as for your application's input/output data.

## Quick example

This heavily annotated example demonstrates what an environment file looks like. It runs a simple 2-part Python application that displays a web page.

```YAML
name: basic-python    # environment name
environment:  # This is the main section where you describe the environment
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
      cmd: "/bin/bash /home/data/launch_scripts/launch_master.sh"   # Optional start command to be run in the container
      ports: "8888"        # Expose container port 8888 as 8888 on the host
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
    service: 8888:master:8888
    # An optional custom message to display to the user once the port is exposed.
    # The "{url}" field is replaced by an HTTP url to the tunnel
    message: "To access the master, use this URL: {url}"
```
### Components

Components are the fundamental building blocks of a Clusterous application. In the above example, there are two components, a "master", and an "engine" with multiple instances.

A more realistic application may typically contain three components: a master component that handles input parameters, a queue component that accepts jobs from the master, and a worker component that takes jobs from the queue and returns results to it. In such a case, the master and queue would both run on the "master" node, and multiple instances of workers would run on the "worker" nodes. Care must be taken to configure the ports such that all components can talk to each other.

### Organising files
When creating an environment file, it may be best to group all necessary files in a simple directory structure for easy management. For example, the above example may be placed like the following:
```
basic-python/
--image/
  --Dockerfile
--launch_scripts/
  --launch_master.sh
  --launch_engine.sh
--basic-python-env.yml      # the environment file itself
```
Again, it is important to note that paths you specify inside the environment file are relative to the location of the environment file itself. Therefore, the above environment file implies that folders are laid out in this way.

### Image and cmd
The `image` field under the components is the same as what you would provide to Docker to run a standalone container. If the image specified is on the Docker Hub, it will automatically be pulled and run. If the image is your own and has been built by the top level `image` field, it would have been placed in the private docker registry of your account. Access the image with the `registry:5000/` prefixed to its name, as per the above example.

The optional `cmd` field runs a command on the container on launch. In the above example, the appropriate launch shell script is run, which in turn starts the servers. Some containers do not need an explicit command if they already have a background service running. In such cases, the `cmd` field can be omitted.

### CPU, Memory and Count
The `cpu` field is mandatory and is either set to "auto" or an explicit number (decimals are allowed; 0.5 means half a CPU). Note that there are some limitations what you specify as described in the section Component Resources.

The `count` field is optional, defaulting to 1 instance. If specified, the only value currently accepted is "auto", which means Clusterous will create as many instances as possible on the given machine type, ensuring maximum utilisation.

There is currently no way to specify memory: memory is assigned to each component (or instance) proportionally based, on the CPU.

### Count vs CPU: The limitations
A key feature of Clusterous is that you don't directly specify how many instances of a component you want running. A component either has one running instance (which may run on the same machine as one or more components), or multiple instances, the exact number of which is automatically determined. In a typical application, this would mean that components such as a UI, master and queueing system would have a single instance each, whereas workers would have as many instances as possible given the cluster size.

A consequence of this is that when specifying the `cpu` field or `count` field for a component, there are certain combinations that are not permitted. For example, when running two different component on the same machine (like a UI and a queue), `cpu` for those components must be set to "auto", indicating that the CPU will be evenly divided among components. On the other hand, for a typical "worker" component, `count` will be "auto", and an explicit `cpu` must be specified.

### Mapping Ports
The `ports` field supports a few different syntax options for exposing the container's ports on the host. Multiple ports can be specified in the form:

```YAML
  ports: 2000,2001,2002
```

The above example will map the three container ports to the same port on the host. If you want to specify a different port number for the container and the host, simply separate them with a colon, in the form host_port:container_port:

```YAML
  ports: 2000:8000,2001:8001,2002:8002
```

### Network mode
By default, components' Docker containers run with the Docker "bridge" network that is suitable for running many similar containers on one node. However, for some containers, it may be necessary to use Docker's "host" network mode, which runs the container on the same network as the underlying node.

Most of the time the default "bridge" network is appropriate, but if your application has particular networking requirements, you can set a component Docker container to run in "host" mode. This can be achieved by the `docker_network` field under a component, which accepts one of two values: `bridge` (default) and `host`. When running in "host" mode, port mappings are not applicable (since the container use's the node's network, any ports opened inside the container are effectively opened on the node itself).

An example of a component running in `host` mode:

```YAML
    master:
      machine: master
      cpu: auto
      image: registry:5000/basic-python
      cmd: "/bin/bash /home/data/launch_scripts/launch_master.sh"\
      docker_network: host
```

### Expose Tunnel
The `expose_tunnel` element is used for creating an SSH tunnel between your local machine and a running component on the cluster in order to expose a service such as a web UI. The `service` field lets you specify the ports and the components in the format `local_port:component_name:source_port`, where `local_port` refers to the port to be created on your local machine.

You can optionally specify a `message` field to display a custom message to the user when the environment is run and the tunnel has been created. The message can include the special `{url}` and `{port}` strings, which Clusterous substitutes with a correctly generated URL or port. In the above example, after the environment has been run, a message of the following type will be displayed:

```
To access the master, use this URL: http://localhost:8888
```

If instead of exposing a web application, your tunnel exposes an HTTP queueing system, you may only want to print the port it is available on. For example a message in this form will display the local port you specified in the `service` field:

```YAML
  message: "The queueing system is available on localhost on port {port}"
```

It is also possible to expose multiple tunnels under `expose_tunnel` by using a YAML list of dictionaries, for example:

```YAML
  expose_tunnel:
    - service: 8080:notebook:8080
      message: "Notebook is available at {url}"
    - service: 9090:console:9090
      message: "Console is available at {url}"
```


## Launching

The above example (with all associated files) is available in the Clusterous source under `subprojects/environments/basic_demo`.

To run the environment once your cluster has started, use the `run` command, passing in the environment file. For example:

```
$ clusterous run subprojects/environments/basic_demo/basic_env.yml
```

The optional `--verbose` switch can be used to show more information about what is happening.

The first time you run this example, Clusterous may have to build the Docker image, which may take a few minutes. Additionally, there will be a few minute's wait when deploying the applications while the nodes download the newly built Docker image from the cluster's repository. Note that on subsequent runs on the same cluster, this delay doesn't happen as the nodes will be able to use a cached copy of the image.

Clusterous will first copy the specified directories to the shared storage, build the image(s) if necessary, before going on to run the containers. Since the environment file has an `expose_tunnel` section, the following will be output on the terminal when the environment has finished launching:

```
Message for user:
To access the master, use this URL: http://localhost:8888
```

Visit that URL in a browser and you will see a web page with a directory listing, confirming that the environment has been launched.

To kill the launched environment, use the `quit` command:

```
$ clusterous quit
```

Upon confirmation, Clusterous will kill the running container processes and destroy any SSH tunnel from your machine to the cluster. The `quit` command leaves the built Docker image(s) untouched, and does not delete any files from the shared storage.

To stop the cluster itself, use the `destroy` command.


## Next steps
A more sophisticated example is available under `subprojects/environments/ipython-lite`. This example runs a configured IPython Parallel environment, and includes three different intercommunicating components and a number of configuration files.
