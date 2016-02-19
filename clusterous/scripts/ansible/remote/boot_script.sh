
n=0
while [ $n -le 60 ]
do
   ansible-playbook -c local {{ playbook }} >>/tmp/startup.log
   if [ $? -eq 0 ]
   then
      break
   fi
   n=`expr $n + 1`
   sleep 5
done
