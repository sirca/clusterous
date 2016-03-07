# Central Logging
Here we describe what is the Central logging system, why it is important and how to use it.

## What is it?
It is a virtual machine running inside the cluster that collects system logs from the entire cluster. This virtual machine has been cofigured with the ELK (Elasticsearch, Logstash and Kibana) components which makes possible the central logging system. Clusterous creates a secure connection (SSH tunnel) between your computer and the central logging virtual machine so you can browse the centralised logs from your computer.

## Why it is important?
It potentially can help you identify problems on the cluster, debug your code, collecting timestamp and events from logs, inspect logs from services running on the cluster and many other benefits that comes from having a centralised logging system.

## How to setup?
It is very simple to setup. Just add ```central_logging_level: 2 ``` to your parameters file and then create your cluster. The value ```2``` means collecting system logs from the virtual machines plus your applications. The value ```1``` collects system logs from virtual machines only. 

To send logs from your application to the central logging system you have to have rsyslog installed inside yur docker container. Then add ```*.* @central-logging:5514``` to ```/etc/rsyslog.conf``` and restart the rsyslog service. An example is available in clusterous repository under ```subprojects/environments/central-logging-sample``` folder.

## How to use it?
Once your cluster has been created with a centralised logging you have to issue the ```logging``` Clusterous command. It will present you the URL to access the UI of the centralised logging system. This UI allows you to search and filter the logs, customise the views, create charts and much more. You can find more information how to use Kibana [here](https://www.elastic.co/products/kibana).

## How to delete it?
The centralised logging virtual machine and its logging information will be destroyed when you destroy the cluster. A good practice is to export your logs before destroying the cluster.
