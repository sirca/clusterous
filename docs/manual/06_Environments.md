# Environments: Running your application

Clusterous is designed around Docker, which is a technology and suite of tools for running lightweight application "containers".

This document is a guide to running your Docker-based cluster application on a Clusterous cluster.

## Do you need to create an environment file?
An environment file is a script that tells Clusterous how to deploy a multi-part Docker-based cluster application.

You do not need to create your own environment file if you can instead use an existing one. For example, if you just want to use IPython Parallel via the IPython notebook, you can use the IPython Parallel environment that the Clusterous team has already developed: just add your own code and data. Similarly, other users may have developed Clusterous environments for other parallel compute frameworks; it may be possible to just run them and copy your code/data over to the cluster.

If none of the existing environments suit you, or if you need to customise an existing environent, you need to understand environment files.

## Prerequisites
This guide assumes you are familiar with Docker and have already made your application run in a Docker container in a test environment. Refer to [Appendix 3](A03_Docker.md) for information on getting started with Docker.

## Background
In order to deploy an parallel compute application on to a compute cluster, a number of actions must take place. They including many or all of the following:

- building an updated Docker image (or images) for your application and making them available on the cluster
- copying any additional files that your application needs, but hasn't been included in the Docker images. These may include configuration files, launch scripts, input data, etc.
- running all the Docker containers correctly, across all the nodes in the cluster, with each using the appropriate resources, etc.
- a connection between the client machine and the cluster; if your application has a web based interface (e.g. the Jupyter notebook) or any other kind of external interface, you need to be able to easily access it

The Clusterous "environment file" feature provides an easy way to achieve all of the above with a single step.

## Environment files
An environment file is a special YAML format file that you write, allowing you to deploy and run your application on the cluster in a single step.

The environment file is passed to the `run` command to run the environment on the current cluster. Alternatively, it can be specified in the cluster parameters file, such that the environment is run as soon as the cluster is created.

We will work through what goes into an environment file by means of an example. We will use the basic-python example available under (https://github.com/sirca/clusterous/tree/master/subprojects/environments/basic-python). This environment runs a simple 2-part Python application that displays a web page.

The following is the contents of the heavily annotated basic-python-env.yml environment file:

```YAML
name: basic-python    # environment name
environment:  # This is the main section where you describe the environment
  # Copy any necessary folders to the cluster shared storage.
  # The folder name is relative to the location of this environment file
  copy:
    - "launch_scripts/"        # the launch_scripts directory is in the same location as this file
  # Build one or more Docker images. If an image of the same name already exists
  # in your private Docker registry, it won't be built.
  # Again, this folder is relative to the location of this environment file.
  image:
    - dockerfile: "image/"   # folder containing Dockerfile
      image_name: "basic-python"    # name of the image
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

As can be seen in the above example, the environment file refers to some other files that form part of the application environment. The directory structure of the basic-python directory illustrates.

```
basic-python/
├── basic-python-env.yml        # the environment file itself
├── image/
│   └── Dockerfile
└── launch_scripts/
    ├── launch_engine.sh
    └── launch_master.sh
```

Where possible, it is recommended to place all files associated with an environment under a single directory, to enable easy bundling and redistribution. Again, it is important to note that paths you specify inside the environment file are relative to the location of the environment file itself.

The environment file effectively acts like a special script, carrying in sequence a number of different actions that you describe. The following sections document the different parts of environment files.

### `environment`
Apart from `name`, the other top level section in the environment file is `environment`. This is the main section under which you describe to Clusterous how to deploy your application.

### Copy and image
The `copy` field under `environment` tells Clusterous to copy some files from your computer to the cluster's shared volume. It runs before any containers are deployed, and works similar to Clusterous' `put` command. In this example, we copy the the `launch_scripts` directory and all of its contents to the cluster's shared volume. On the cluster, the shared volume is available under `/home/data`.

The next field is `image`, which, if provided, lets you build your Docker images on the cluster. As shown, provide a list of docker images to be built; for each image, provide the `dockerfile` and `image_name`.

### Components
Components are the fundamental building blocks of a Clusterous application. In this example environment file, there are two components, a "master", and an "engine" with multiple instances.

A more realistic application may typically contain three components: a master component that handles input parameters, a queue component that accepts jobs from the master, and a worker component that takes jobs from the queue and returns results to it. In such a case, the master and queue would both run on the "master" node, and multiple instances of workers would run on the "worker" nodes. Care must be taken to configure the ports such that all components can talk to each other.

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
Cluster applications often have one or more components that open a networking port so that they can accept incoming connections. For example, a web based notebook would accept connections from a web browser, or a queueing system would expose a REST API for adding and removing items. Since these processes run inside a Docker container, it is necessary to use Docker's port mapping feature; this will allow a port on the container to be exposed on the host machine.

**Note**: Docker containers in Clusterous can only expose ports in the range 1024-65535 (inclusive), meaning that any exposed ports must be in the above range. In practice, this is only of concern if any part of your application uses a well-known port (<1024). If so, you must be able to customise your component process to only use ports between 1024-65535.

The `ports field is used for exposing ports on a Docker container. The field supports a few different syntax options for exposing the container's ports on the host. Multiple ports can be specified in the form:

```YAML
  ports: 2000,2001,2002
```

The above example will map the three container ports to the same port on the host. If you want to specify a different port number for the container and the host, simply separate them with a colon, in the form host_port:container_port:

```YAML
  ports: 2000:8000,2001:8001,2002:8002
```

### Network mode
By default, components' Docker containers run with the Docker "bridge" network that is suitable for running many similar containers on one node. However, for some containers, it may be necessary to use Docker's "host" network mode, which runs the container on the same network as the underlying node.

Most of the time the default "bridge" network is appropriate, but if your application has particular networking requirements, you can set a component Docker container to run in "host" mode. This can be achieved via the `docker_network` field under a component, which accepts one of two values: `bridge` (default) and `host`. When running in "host" mode, port mappings are not applicable (since the container use's the node's network, any ports opened inside the container are effectively opened on the node itself).

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

The above example (with all associated files) is available in the Clusterous source under `subprojects/environments/basic-python`.

To run the environment once your cluster has started, use the `run` command, passing in the environment file. For example:

```
$ clusterous run subprojects/environments/basic-python/basic-python-env.yml
```

The first time you run this example, Clusterous may have to build the Docker image, which may take several few minutes. The build process can be speeded by using the `controller_instance_type` in the cluster parameters file (See [Chapter 5](05_Create_and_destroy.md).

Additionally, there will be a few minute's wait when deploying the applications while the nodes download the newly built Docker image from the cluster's repository. Note that on subsequent runs on the same cluster, this delay doesn't happen as the nodes will be able to use a cached copy of the image.

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

## Preparing your application for Clusterous
The first step to running your application on Clusterous is determining its architecture. Cluster applications tend to have multiple parts, whether they use existing frameworks (such as IPython Parallel) or use a custom-built one. Once you have determined the different parts (components), you need to run each component of the application in its own Docker container.

The workflow for running your application on Clusterous would typically follow a similar pattern:

- Place your application's components in Docker containers
- Run the containers on your personal machine, ensuring that they run individually and can communicate with each other. This test run would of course be a scaled-down version of the cluster application (fewer workers)
- Write the environment file for your application in order to run it on the cluster

There are some requirements to be aware of for Clusterous applications:

- If a component opens a network port, it must be in the range 1024-65535. If your application uses other ports, you need to be able to customise it to use one within this range.
- The shared volume is automatically mounted on /home/data on all containers. If you need to place configuration files or input data on the shared volume, you need to be able to tell your application where to find them.

If you port a popular framework to run on Clusterous, it may be best to leave your own code out of the environment itself. A lot of the power of Clusterous environments comes from reusability, so a general purpose environment may be useful to many people.

## IPython example
A more sophisticated example is available under `subprojects/environments/ipython-lite`. This example runs a configured IPython Parallel environment, and includes three different intercommunicating components and a number of configuration files.

## Custom clusters
By default, the cluster launched by Clusterous has a standard master/worker architecture, consisting of 1 master node and `n` worker nodes. While this suits a wide range of applications, there are many cases where a more complex or sophisticated layout is necessary. Clusterous allows defining custom cluster architectures via the environment file.

### Examples
To define a cluster layout, create a top-level `cluster` element in the environment file, and populate it with groups of nodes. To illustrate, this example defines a layout identical to the default master/worker layout:

```YAML
cluster:
  master:
    type: $master_instance_type
    count: 1
  worker:
    type: $worker_instance_type
    count: $worker_count
```

As can be seen, under the `cluster` element are two elements defining the names of the two types of nodes: `master` and `worker`. Under each, there are two mandatory fields: `type` and `count`, corresponding to the instance type and the number of instances. Under `master`, `count` is set to `1`, meaning that there is always exactly 1 master node. All the other values are represented by a dollar sign followed by an identifier. These are variables, meaning that each is replaced by an actual value.

Where are these variables assigned values? If you look closely, you'll note that the names are identical to those defined in the parameters file used for cluster creation. In theory, you could put fixed values for `type` and `count`, but using variables allows those choices to be made during cluster creation. This feature is especially useful when distributing your environment files for other users to use; they do not need to understand the details of the environment file, and can simply supply the required value in the `parameters` section of the parameters file.

Note that variables are defined dynamically. In other words, no seperate declaration is needed: simply use the variable, and Clusterous will substitute the value provided in the parameter file.

The use of variables is not restricted to the `cluster` section of the environment file. For instance, in the above environment example, you could require users to supply a "cpus_per_engine" value by setting the `cpu` value for the `engine` component to `$cpus_per_engine` instead of 0.5.

The following example shows are more complex layout, for a hypothetical application that uses separate groups of specialised CPU-bound workers and IO-bound workers:

```YAML
cluster:
  master:
    type: $master_instance_type
    count: 1
  io_master:
    type: $io_master_instance_type
    count: 1
  cpu_worker:
    type: $cpu_worker_instance_type
    count: $cpu_worker_count
  io_worker:
    type: $io_worker_instance_type
    count: $io_worker_count
```

Here we have defined four different types of nodes consisting of two separate "masters" and two groups of workers. Of course, the `environment` section would have to ensure that application components are correctly deployed to each node types. This example uses six different variables, all of which have to be supplied in the parameters file. The `parameters` section of the parameters file might look like this:

```YAML
parameters:
  master_instance_type: t2.medium
  io_master_instance_type: m4.large
  cpu_worker_instance_type: c4.large
  cpu_worker_count: 12
  io_worker_instance_type: i2.xlarge
  io_worker_count: 6
```

