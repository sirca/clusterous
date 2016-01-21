#!/bin/sh

# Spark 
if [ ! -d /home/data/spark ]; then
	wget -nc http://archive.apache.org/dist/spark/spark-1.4.0/spark-1.4.0-bin-hadoop2.4.tgz
	tar zxvf spark-1.4.0-bin-hadoop2.4.tgz
	mv spark-1.4.0-bin-hadoop2.4 /home/data/spark
    mv /home/data/files/spark-env.sh /home/data/spark/conf
	mv spark-1.4.0-bin-hadoop2.4.tgz /home/data/http
else
    echo "Spark already configured"
fi
