for i in $(docker ps|grep -v CONTAINER| awk '{print $1}'); do docker inspect $i |if grep MARATHON_APP_ID=/$1 >null;then echo $i;fi; done
