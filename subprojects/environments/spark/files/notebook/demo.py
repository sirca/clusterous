import pyspark

conf = pyspark.SparkConf()
conf.setMaster("mesos://controller:5050")
sc = pyspark.SparkContext(conf=conf)
sc.parallelize([1, 2, 3, 4, 5]).count()
