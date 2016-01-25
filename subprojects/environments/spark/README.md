## Spark Environment

This environment gives you an IPython notebook connected to spark instances running inside the cluster (see diagram below).
By default it creates 2 spark instances. You can modify the number and type of spark instances in the [spark-cluster.yml](spark-cluster.yml) file.

A trivial Python example has been added to the IPython notebook folder.

### Launch

```shell

clusterous create spark-cluster.yml
```
Afeter successful cluster creation it will show the link to access the IPython notebook.

#### Note: 
It takes time to create the cluster and configure spark. It may take up to 20 minutes to have the IPython notebook available.

### Diagram
![](misc/clusterous-spark-v2.png)
