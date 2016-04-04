# Quick start

This chapter will show you how to install and configure Clusterous so that you can start using it.

## Installation

### Preparation
To install Clusterous, you need Python 2.7 and the associated package management tool "pip". Many systems already have Python and pip installed, so enter the following on the command line to check:

    python --version

If you do have the correct version of Python installed, the above command should simply output someething like `Python 2.7.9`. If Python is not installed, use your system's package management tool to install Python 2.7 and run the above command again.

Next, ensure you have pip installed:

    pip --version

If you do have pip installed, you will pip's version number. If not, install pip using your system's package management tool. General instructions for obtaining pip are available here: (https://pip.pypa.io/en/stable/installing/).

**Note on Python versions**: Some systems may have Python 3.x installed. Python 3.x is a separate, incompatible version of Python that cannot run Clusterous. You can however have both Python 2.7 and 3.x installed on the same system. If you have both versions, the `pip` command may by default point to the Python 3.x version, which can be confirmed by running `pip --version`. Once you have Python 2.7 installed, the appropriate version of pip can be run as `pip2`. You can verify this with:

    pip2 --version

Make sure you use `pip2` to install Clusterous.

### Clusterous
Install Clusterous using the following command.

    sudo pip install clusterous


### Verify

To verify that Clusterous is installed, try:

    clusterous --help
    
And you should see Clusterous' help output. Like a typical Unix command line tool, it should show you the list of commands and options.

## Configuring
Clusterous creates clusters on your own AWS account, so before you start using Clusterous, you need provide your AWS credentials and run the interactive Clusterous setup wizard.

The AWS keys are in the form of an Access Key ID and Secret Access Key, and are provided to you by AWS when you create an IAM user in your AWS account. You may refer to [this manual's guide](A02_AWS.md) to preparing your AWS account for use. Your AWS credentials will typically look something like:

    Access Key ID: AKIAIOSFODNN7EXAMPLE
    Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY

Once you have obtained your AWS keys, run the `setup` command to launch the interactive wizard:

    clusterous setup

The setup wizard will start by asking you to enter your AWS keys (which you can copy/paste into the terminal). Following that, it will guide your through setting up some AWS resources that Clusterous needs for launching and managing clusters. In each case, Clusterous will give you the option of either picking an existing one or creating a new one. In general, if you expect to share your clusters with collaborators, it is recommended that you use the same resources as them. If you are the first to use Clusterous on your account, or will be working alone, feel free to create your own resources using the setup wizard. To quit the setup wizard at any time, enter `Ctrl-C`.

Some of the questions the setup wizard will ask for:

- The AWS region you want to use. This corresponds to the location of their data centers, and you would typicaly choose the one geographically nearest to you.
- The VPC (Virtual Private Cloud) to use, which pertains to AWS networking. If you are the first to use AWS on your account, feel free to create a new one. If a colleague is already using Clusterous on your account, it is best to choose the same one as them
- A Key Pair, which is an SSH key for establishing a secure connection to your cluster. Clusterous needs a `.pem` key file to create and manage clusters. Like with VPCs, it is best to use an existing Key Pair if you are collaborating with others on your account. If chosing an existing Key Pair, Clusterous will ask you for the location of your key file.
- An S3 bucket for storing Docker images. Like with other resources, you are best off sharing the S3 bucket with collaborators. Note that S3 bucket names are global across AWS, so people typically prefix their organisation name.
- A name for this configuration profile. You need only one profile to begin with. Clusterous lets you have multiple sets of configuration, which is useful if you run on multiple regions or AWS accounts.

Once you have succesfully run the setup wizard, you are ready to start using Clusterous.

## Creating a cluster
You are now ready to create your first cluster using Clusterous. To create a cluster, you need to provide Clusterous some information via a _cluster parameters file_ that you create. This information includes the number of virtual machines, their types, as well as a name for the cluster.

Create a new `.yml` file using your preferred plain text editor. For example, if you use `vi`, type:

    vi mycluster.yml

Place the following contents to the file:

```yaml
cluster_name: mycluster
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```

Replace `mycluster` with an appropriate name (e.g. `bob-cluster` or `physics-cluster`). The name must be alphanumeric, dashes are supported.

The above parameters will instruct Clusterous to create a cluster of the default master/worker type, all running AWS `t2.micro` nodes. In the default master/worker architecture, there is always 1 master and any number of workers. For the sake of demonstration, we will have 2 workers for now.

Create the cluster by entering:

    clusterous create mycluster.yml

Where `mycluster.yml` is the name of the cluster parameters file you created.

Clusterous display some progress output on the screen as it creates and configures the cluster on your AWS account. The creation takes a few minutes, after which Clusterous will return you to the command prompt.

Once the `create` command finishes, run the `status` command to get an overview of your cluster:

    clusterous status

This should output something resembling the following:

```
mycluster has 5 instances running, including nat and controller
Uptime:     9 minutes

Controller
IP: 52.0.0.0  Port: 22000

Node Name     Instance Type      Count  Running Components
[controller]  t2.small               1  --
[nat]         t2.micro               1  --
worker        t2.micro               2  [None]
master        t2.micro               1  [None]

Shared Volume
45M (1%) used of 20G
19G available
```

The `status` command shows you, amongst other things, the number and types of nodes running on your cluster. Note the special `Controller` and `NAT` instances: these are part of each cluster and assist in the networking and management of the cluster, and you can safely ignore them for now.

You now have a working Clusterous cluster running on AWS.

Next, we will run an example application on the cluster. In Clusterous, an "environment" refers to a Docker based application, along with any associated configuration and data. The [Clusterous source repository](https://github.com/sirca/clusterous/) has a couple of example environments, one of which we will use. Download the `subprojects/environments` directory, within which you will find the `ipython-lite` directory containing the `ipython.yml` file. Take note of the location. The `ipython-lite` environment will run [IPython Parallel](http://ipyparallel.readthedocs.org/en/stable/), which combines the popular IPython web-based Python notebook (now known as Jupyter) with a parallel compute framework.

Use the `run` command to launch the environment on the current running cluster. To launch, use the following (substituting the appropriate file path):

    clusterous run environments/ipython-lite/ipython.yml

When you run this, it will take a few minutes to copy some files over to your cluster, build a Docker image on the cluster, run IPython Parallel across the master and workers, and then create an SSH tunnel so that you can access the web-based notebook from your computer. Once the command finishes running, you should see output similar to this:

```
Message for user:
The IPython engines may take up to 30 seconds to become available.
The connection file is located at:
/home/data/ipython/profile/security/ipcontroller-client.json
To access IPython notebook, use this URL: http://localhost:8888
```

Wait a few seconds for it to finish launching, and go to http://localhost:8888 in your web browser. You should be able to see the interactive Jupyter notebook running on the Cluster. If you are familiar with IPython, you should be able to play around with the example notebook, or create a new one.

## Finishing
Once you are done, destroy the cluster you created using the `destroy` command:

    clusterous destroy

After asking for your confirmation, Clusterous will destroy the cluster and you will stop being billed for EC2 usage.

