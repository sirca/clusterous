# Central Logging
Clusterous can optionally provide a central logging system which can be used to diagnose problems with your application. The central logging system runs as a dedicated virtual machine in your cluster, and is accessible to all nodes.

If enabled, you can access the logs on the central logging system using a web-based interface. The logging system itself runs the popular "ELK" stack (Elasticsearch, Logstash and Kibana).

How your application uses the logging sytem is up to you. Many libraries and frameworks will already have some in-built logging. If your application logs errors it encounters, you can for example, identify issues your components have in communicating with each other.

## Enabling the central logging system
The logging system can be enabled in the cluster parameters file. Add the field `central_logging_level` to the cluster parameters file:

```yaml
cluster_name: mycluster
central_logging_level: 2
parameters:
    master_instance_type: t2.micro
    worker_instance_type: t2.micro
    worker_count: 2
```

The `central_logging_level` accepts two possible values: `1` or `2`. If set to `1`, only application level logs are collected. If set to `2`, all system level logs are included. A setting of `1` is usually adequate for diagnosing problems with Clusterous applications.

## Logging to the central logging system
To send logs from your application to the central logging system, you must first have `rsyslog` installed inside yur Docker container. Add `*.* @central-logging:5514` to `/etc/rsyslog.conf` inside your container and restart the rsyslog service. An example is available in  theClusterous repository under `demo/central-logging-sample` folder.

## Accessing the web interface
Once your cluster has been created with a centralised logging, use the `logging` command to access it. The `logging` command creates an SSH tunnel between your machine and the logging instance on your cluster, and presents you with the URL to access it. Opening the URL in your web browser gives you the logging system's UI, which allows you to search and filter the logs, customise the views, create charts and more. The UI is powered by Kibana, and you can find more information [here](https://www.elastic.co/products/kibana).

## Deleting the logging system
The central logging system's virtual machine and all its logging information is destroyed when you destroy the cluster. You may choose to export your logs before destroying the cluster.
