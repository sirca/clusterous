import pyspark
import os

os.environ['SPARK_HOME'] = '/home/data/spark'
os.environ['PYTHONPATH'] = '$SPARK_HOME/python:$SPARK_HOME/python/lib/py4j-0.8.2.1-src.zip'

conf = pyspark.SparkConf()
conf.setMaster("mesos://controller:5050")
conf.set("spark.executor.uri", "http://http.marathon.mesos:8881/spark-1.4.0-bin-hadoop2.4.tgz")
sc = pyspark.SparkContext(conf=conf)
time.sleep(10)
sc.parallelize([1, 2, 3, 4, 5]).count()
