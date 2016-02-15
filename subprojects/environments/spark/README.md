## Spark Environment

This environment gives you an IPython notebook connected to spark instances (see diagram below).

By default it creates a cluster with 2 spark instances but you can modify using the [spark-cluster.yml](spark-cluster.yml) file. 

Some examples has been added to the IPython notebook folder so you can start coding from there.

### Launch

```shell

clusterous create spark-cluster.yml
```
After successful cluster creation it will show the link to access the IPython notebook.

### Diagram
![](misc/clusterous-spark-v3.png)
