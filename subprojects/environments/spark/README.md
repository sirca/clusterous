## Spark Environment

This environment gives you an IPython notebook connected to spark instances (see diagram below).

By default it creates a cluster with 2 spark instances but you can modify using the [spark-cluster.yml](spark-cluster.yml) file. 

A trivial Python example has been added to the IPython notebook folder so you can start coding from there.

### Launch

```shell

clusterous create spark-cluster.yml
```
After successful cluster creation it will show the link to access the IPython notebook.

It takes time to create the cluster and configure spark, expect to have the IPython notebook up and running in about 20 minutes after creating the cluster.

### Diagram
![](misc/clusterous-spark-v2.png)
