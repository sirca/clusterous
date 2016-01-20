# Spark binaries
wget -nc http://archive.apache.org/dist/spark/spark-1.4.0/spark-1.4.0-bin-hadoop2.4.tgz
tar zxvf spark-1.4.0-bin-hadoop2.4.tgz
mv spark-1.4.0-bin-hadoop2.4 /home/data/spark

# Spark configuration
mv /home/data/files/spark-env.sh /home/data/spark/conf

# Http server
mkdir -p /home/data/http
wget -nc http://www.apache.org/dyn/closer.lua/spark/spark-1.4.0/spark-1.4.0-bin-hadoop2.4.tgz
mv spark-1.4.0-bin-hadoop2.4.tgz /home/data/http
cd /home/data/http; python -m SimpleHTTPServer 8881
