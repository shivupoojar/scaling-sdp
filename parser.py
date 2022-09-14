#!/usr/bin/env python
# coding: utf-8

# In[1]:


#get_ipython().system('pip3 install minio')
#get_ipython().system('pip3 install pandas')
#get_ipython().system('sudo apt-get install -y mosquitto-clients')


# In[2]:


import sys
import  datetime
import os
from minio import Minio
import csv
import json
import pandas as pd
import time
import subprocess
from subprocess import Popen, PIPE
import requests
from IPython.display import display


# In[3]:


#df_metrics = pd.DataFrame(columns=['Workload_size','Workload TPT','Average Workload TPT','Average FET','Average CT'])


# In[4]:


scenario="namespace_async_conf"
user=int(sys.argv[1])
iteration=int(sys.argv[2])
minio_host="172.17.141.197:9001"
bucket_name="aeneas-output"
PROMETHEUS = 'http://172.17.141.197:9096/'


# In[5]:


cmd = "./mqtt_client.sh "+str(user)
with Popen(cmd, stdout=PIPE, stderr=None, shell=True) as process:
    output1 = process.communicate()[0].decode("utf-8")
time.sleep(180)


# In[6]:


df= pd.read_csv('mqtt.csv')
print(df)


# In[7]:


#Minio Client
client = Minio(minio_host, access_key = "minio", secret_key ="minio123",secure=False)
# List objects from the bicket and notedown time  stamp  when they stored
objects = client.list_objects(bucket_name,recursive=True)
outtime = []
for obj in objects:
    outtime.append(obj.last_modified)
    client.remove_object(bucket_name, obj.object_name)


# In[8]:


df['outtime']= outtime
df['outtime']= pd.to_datetime(df['outtime']).dt.tz_convert(None)
df['intime']= pd.to_datetime(df['intime'])
df =df.sort_values(by="outtime")
display(df)
print(df['outtime'].iloc[-1]-df['intime'].iloc[0])


# In[ ]:


def get_function_execution_time(cmd):
    with Popen(cmd, stdout=PIPE, stderr=None, shell=True) as process:
        return (process.communicate()[0].decode("utf-8"))    


# In[ ]:


#cmd1 = "sudo kubectl logs gateway-7b8d9dbb5b-rhnwl  -n openfaas -c gateway | grep getobject | cut -c 71-77 | tail -"
cmd1="ssh ubuntu@172.17.141.197 "+"sudo kubectl logs gateway-7b8d9dbb5b-ggwl6  -n openfaas -c gateway  | grep scaling-aeneas-mqtt | cut -c 94-97 | tail -"+str(len(outtime))
cmd2="ssh ubuntu@172.17.141.197 "+"sudo kubectl logs gateway-7b8d9dbb5b-ggwl6  -n openfaas -c gateway  | grep scaling-aeneas-tocloud | cut -c 96-101 | tail -"+str(len(outtime))
df['aeneas']=(get_function_execution_time(cmd1)).split("\n")[:-1]
df['tocloud']=(get_function_execution_time(cmd2)).split("\n")[:-1]


# In[ ]:


#TPT: Total Processing Time
#FET: Function Execution Time
#CT: Communication Time
df =df.sort_values(by="outtime")
df['TPT']=(df['outtime']-df['intime']).dt.seconds
df['FET'] = (df['aeneas']).astype(float) + (df['tocloud']).astype(float)
df['CT']= (df['TPT']).astype(float) - df['FET']

display(df)
df.to_csv("data/"+str(user)+"_"+str(iteration)+"_"+scenario+".csv")


# In[ ]:


metrics = {'workload_type':str(user)+"_"+scenario,'workload_size':user,'Workload TPT':df['TPT'].sum(),'Average Workload TPT':df['TPT'].mean(),'Average FET':df['FET'].mean(),'Average CT':df['CT'].mean()}
print(metrics)


# In[ ]:


pre_url = PROMETHEUS + '/api/v1/query?query='
timestamp= pd.to_datetime(df['outtime'].iloc[-1], format='%Y-%m-%d %H:%M:%S')
time = (time.mktime(timestamp.timetuple()))
#interval= int(df['TPT'].sum()) if int(df['TPT'].sum()) > 60  else 60


# In[ ]:


interval = (df.loc[user-1, 'outtime'] - df.loc[0, 'intime']).total_seconds()
interval= round(interval)


# In[ ]:


def getdataprometheus(url):
    headers= {"Accept": "application/json"}
    res = json.loads(requests.post(url=url, headers=headers).content.decode('utf8', 'ignore'))
    data=res.get('data').get('result')[0].get('value')[1]
    return data


# In[ ]:


expr_cpu='sum(rate(container_cpu_usage_seconds_total{container_name!="POD",namespace=~"openfaas.*|default"}[5m]))&time='+str(time)
expr_memory='sum(container_memory_working_set_bytes{container_name!="POD",namespace=~"openfaas.*|default"})&time='+str(time)
expr_disk_read ='sum(rate(container_fs_reads_bytes_total{namespace=~"openfaas.*|default"}['+str(interval)+'s]))&time='+str(time)
expr_disk_write='sum(rate(container_fs_writes_bytes_total{namespace=~"openfaas.*|default"}['+str(interval)+'s]))&time='+str(time)
expr_network_transmit='sum(rate(container_network_transmit_bytes_total{namespace=~"openfaas.*|default"}['+str(interval)+'s]))&time='+str(time)
expr_network_recieve='sum(rate(container_network_receive_bytes_total{namespace=~"openfaas.*|default"}['+str(interval)+'s]))&time='+str(time)
#expr_cpu = '100 - (avg (irate(node_cpu_seconds_total{mode="idle"}['+str(interval)+'s])) * 100)&time='+str(time)
#expr_memory = '100 - ((sum(node_memory_MemAvailable_bytes) / sum(node_memory_MemTotal_bytes))*100)&time='+str(time)
#expr_disk_read = 'sum(rate(node_disk_read_bytes_total['+str(interval)+'s]))&time='+str(time)
#expr_disk_write =  'sum(rate(node_disk_written_bytes_total['+str(interval)+'s]))&time='+str(time)
#expr_network_transmit= 'sum(rate(node_network_transmit_errs_total{device!~"lo | veth. | docker.* | flannel.* | cali.* | cbr."}['+str(interval)+'s]))&time='+str(time)
#expr_network_recieve='sum(rate(node_network_receive_packets_total{device!~"lo | veth. | docker.* | flannel.* | cali.* | cbr."}['+str(interval)+'s]))&time='+str(time)
metrics['C_CPU'] = getdataprometheus(pre_url+expr_cpu)
metrics['C_RAM'] = getdataprometheus(pre_url+expr_memory)
metrics['C_disk_read']=getdataprometheus(pre_url+expr_disk_read)
metrics['C_disk_write']=getdataprometheus(pre_url+expr_disk_write)
metrics['C_network_recieve']=getdataprometheus(pre_url+expr_network_transmit)
metrics['C_network_transmit']=getdataprometheus(pre_url+expr_network_recieve)


# In[ ]:


#Pod Stats
expr_pod_cpu_aeneas_function = 'sum(rate(container_cpu_usage_seconds_total{container_name!="POD",namespace="openfaas-fn",pod=~"scaling-aeneas-mqtt.*"}['+str(interval)+'s]))&time='+str(time)
expr_pod_cpu_mosquitto_broker = 'sum(rate(container_cpu_usage_seconds_total{container_name!="POD",namespace="default",pod=~"mosquitto.*"}['+str(interval)+'s]))&time='+str(time)
expr_pod_cpu_mosquitto_connector_aeneas = 'sum(rate(container_cpu_usage_seconds_total{container_name!="POD",namespace="openfaas",pod=~"aeneas.*"}['+str(interval)+'s]))&time='+str(time)
expr_pod_cpu_mosquitto_connector_tocloud = 'sum(rate(container_cpu_usage_seconds_total{container_name!="POD",namespace="openfaas",pod=~"tocloud.*"}['+str(interval)+'s]))&time='+str(time)
expr_pod_cpu_functions_all = 'sum(rate(container_cpu_usage_seconds_total{container_name!="POD",namespace="openfaas-fn"}['+str(interval)+'s]))&time='+str(time)


metrics['pod_cpu_aeneas_function']=getdataprometheus(pre_url+expr_pod_cpu_aeneas_function)
metrics['pod_cpu_mosquitto_broker']=getdataprometheus(pre_url+expr_pod_cpu_mosquitto_broker)
metrics['pod_cpu_mosquitto_connector_aeneas']=getdataprometheus(pre_url+expr_pod_cpu_mosquitto_connector_aeneas)
metrics['pod_cpu_mosquitto_connector_tocloud']=getdataprometheus(pre_url+expr_pod_cpu_mosquitto_connector_tocloud)
metrics['pod_cpu_functions_all']=getdataprometheus(pre_url+expr_pod_cpu_functions_all)



# In[ ]:


df_metrics = pd.read_csv("data/"+str(user)+"_namespace_async_metrics.csv")
df_metrics = df_metrics.append(metrics, ignore_index=True)


# In[ ]:


df_metrics.to_csv("data/"+str(user)+"_namespace_async_metrics.csv",index=False)
#df_metrics=df_metrics.sort_values(by="workload_size")
display(df_metrics)


# In[ ]:





