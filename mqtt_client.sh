#!/bin/bash

csvfilename="./mqtt.csv"
filename="p001.mp3"
user=$1
echo $user
echo user,intime > $csvfilename
for (( i=1; i<=$user; ++i )); do
   mosquitto_pub -h 172.17.141.197 -p 32332 -f ${filename}  -t "aeneas" -q 2 &
   intime=`date +"%Y-%m-%d %T.%3N"`
   echo $i,$intime  >> $csvfilename
done;
