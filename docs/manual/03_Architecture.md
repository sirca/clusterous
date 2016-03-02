# Architecture

Here we are describing (at very high level) the components of a **default cluster** created by Cluserous.

![Clusterous Default Cluster Diagram](misc/Clusterous_Default_Cluster.png)

Components:
* **Client:** It represents your laptop or desktop with Clusterous command-line tool installed.
 
* **Amazon Web Services (AWS):** In the diagram it represents the **default cluster** running on AWS cloud platform. Clusterous hides the complexity of launching, configuring and managing virtual machines.

* **Master:** It represents a virtual machine running your application inside a Docker container. Regarding what is running inside the Docker container is up to you. For example you could have a main program that prepares the data, sends the jobs to the workers and then collecting the results. Perhaps you could have a queueing system where your main program submmits the jobs to the queue and the workers gets from it, processes and write the results to the shared volume.

* **Workers:** It represents one or many virtual machines running your application inside Docker containers. Again, what is inside the Docker container is up to you. In the scenario that you use a queueing system here your code could get a job from the queue, process it and write the result to the shared volume.

* **Shared Volume:** By default comes with a shared volume of 20GB. You could change the size upto 16TB as of the time of writing. This shared volume is under "/home/data" and your application have Read/Write access.

* **NAT Gateway:** It provides the security for the cluster. All communication between your laptop/desktop and the cluster is via secure connections (SSH/SSH tunnels) using your AWS security file. All virtual machines running iside the cluster are isoleted from the world.

* **Cluster Controller:** It is kind of "the brain" of the cluster. It know how many virtual machines are available, how much RAM or how many CPUs are available or used on the whole cluster. It is responsable for scheduling/deploying your applications on the cluster (master and nodes) and responding accordingly when adding or removing virtual machines.

* **Central Logging:** It is a web-based central logging system within the cluster. You could use it for debugging or diagnosing problems on your applications. By default it is an **optional** component.

* **Docker Images:** It represents the storage for your Docker images. Currently is stored in a S3 bucket. Everytime you use a Docker image, Clusterous checks if that image is alredy present then uses it otherwise creates one and stores here.
