#!/bin/bash

csvfilename="./mqtt.csv"
filename="p001.mp3"
user=$1
echo $user
echo user,intime > $csvfilename
for (( i=1; i<=$user; ++i )); do
   mosquitto_pub -h 172.17.141.197  -f ${filename}  -t "aeneas" -q 2 &
   intime=`date +"%Y-%m-%d %T.%N"`
   echo $i,$intime  >> $csvfilename
done;

