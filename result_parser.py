import sys
import  datetime
import os
from minio import Minio
import csv
import pandas as pd
import time
import subprocess
from subprocess import Popen, PIPE

user=sys.argv[1]
print(user)
cmd = "./mqtt_client.sh "+user
with Popen(cmd, stdout=PIPE, stderr=None, shell=True) as process:
    output1 = process.communicate()[0].decode("utf-8")
time.sleep(60)
#df= pd.read_csv('metrics.csv')
df= pd.read_csv('mqtt.csv')
#Minio Client
client = Minio("172.17.141.197:9001", access_key = "minio", secret_key ="minio123",secure=False)
# List objects from the bicket and notedown time  stamp  when they stored
objects = client.list_objects("aeneas-output",recursive=True)
outtime = []
for obj in objects:
    #print(obj.object_name)
    outtime.append(obj.last_modified)
    client.remove_object("aeneas-output", obj.object_name)

# Openfaas function execution time
#cmd1 = "sudo kubectl logs gateway-7b8d9dbb5b-rhnwl  -n openfaas -c gateway | grep getobject | cut -c 71-77 | tail -"
cmd1="sudo kubectl logs gateway-7b8d9dbb5b-rhnwl  -n openfaas -c gateway  | grep scaling-aeneas-mqtt | cut -c 93-97 | tail -"+str(len(outtime))
cmd2="sudo kubectl logs gateway-7b8d9dbb5b-rhnwl  -n openfaas -c gateway  | grep scaling-aeneas-tocloud | cut -c 96-101 | tail -"+str(len(outtime))
with Popen(cmd1, stdout=PIPE, stderr=None, shell=True) as process:
    output1 = process.communicate()[0].decode("utf-8")
with Popen(cmd2, stdout=PIPE, stderr=None, shell=True) as process:
    output2 = process.communicate()[0].decode("utf-8")

df['outtime']=outtime
df['aeneas']=output1.split("\n")[:-1]
df['tocloud']= output2.split("\n")[:-1]
df.to_csv("final.csv")
print(df)