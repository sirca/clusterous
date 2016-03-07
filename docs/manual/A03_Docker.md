# Docker

Docker is a technology for building and running lightweight application "containers". A Docker container is a little bit like a virtual machine, in that it provides you a self-contained operating system environment on which you can run your application. You can easily save the state of your container as an "image" and then start it up later, even on another computer. However, unlike with true virtual machines, working with Docker containers is fast and easy. For example a Docker container starts up in mere seconds, whereas a conventional virtual machine would take minutes.

The Docker website has a good [introduction to Docker](https://www.docker.com/what-docker). It must be noted that Docker is entirely based on Linux, and depends on particular Linux kernel features. As such, Docker (and thereby Clusterous) only runs Linux-based applications.

In the context of cluster computing, Docker greatly simplifies the process of deploying and running an application on a foreign machine (in this case, the cluster nodes). In a more traditional scenario, the cluster would offer a particular OS environment (say Debian), and it would be your responsibility to ensure that your software (with all its dependencies) runs in that environment, a difficult and time-consuming task. With Docker, you simply run your software inside a container running an OS environment of your choosing (say Fedora). You can test and run the container on your own machine, and once you're done, deploy it to the cluster, where it will run without any further change.

Docker is easy to install and use, even for people who are not system administrators. The Docker website has a "Getting Started" guide for [Linux](https://docs.docker.com/linux/) and [Mac](https://docs.docker.com/mac/) users.
