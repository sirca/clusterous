PYTHON PACKAGES INSTALLED:
* [Anaconda](http://docs.continuum.io/anaconda/pkg-docs)
* [BDKD-Datastore](https://github.com/sirca/bdkd_datastore/tree/master/datastore)
* [BDKD-Datastore-Wrapper](https://github.com/sirca/bdkd_datastore/tree/master/datastore-wrapper/python)

RUN:
```$ docker run -d -v /root/docker/laser/volume:/home/data -p 8888:8888 laser```

Where:
* ```-d ``` to run the docker in the background
*  ```-v /root/docker/laser/volume:/home/data``` is the volumes mapping. In this example the folder ```/root/docker/laser/volume``` on the host is mapped to ```/home/data``` inside the container. 
* NOTE: ```/root/docker/laser/volume``` SHOULD contain at least:
```
bdkd_datastore.conf -> BDKD datastore configuration file
notebooks -> Folder for your notebooks
```
* ```-p 8888:8888``` is the ports mapping from the Docker container to the host machine.
 
ACCESS THE NOTEBOOK:
Browse the IP of host where the Docker container is running (e.g. 127.0.0.1, localhost, 54.10.23.1) and point to the port ```8888```
e.g. [http://127.0.0.1:8888](http://127.0.0.1:8888)

TESTING:
```
import datastorewrapper
datastore = datastorewrapper.Datastore()
repos = datastore.list('bdkd-sirca-public')
for i in repos:
    print i
```
