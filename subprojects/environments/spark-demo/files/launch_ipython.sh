# Launch ipython notebook
export SPARK_HOME=/home/data/spark
export PYTHONPATH=$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip
ipython notebook --no-browser --port 31888 --ip=* --notebook-dir=/home/data/files/notebook
#IPYTHON_OPTS="notebook --no-browser --port 31888 --ip=* --notebook-dir=/home/data/files/notebook" /home/data/spark/bin/pyspark --master mesos://controller:5050