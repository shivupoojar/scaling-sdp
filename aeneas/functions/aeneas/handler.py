#from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from aeneas.tools.execute_task import ExecuteTaskCLI
import requests
import json
import random
import os
import paho.mqtt.publish as publish

def save_file(filename, data):
    with open("/tmp/"+filename, "wb") as out_file:
      out_file.write(data)
def handle(req):
    """handle a request to the function
    Args:
        req (str): request body
    """
    save_file("a.wav",req)
 #   config_string = u"task_language=eng|is_text_type=plain|os_task_file_format=json"
 #   task = Task(config_string=config_string)
 #   task.audio_file_path_absolute = req
 #   task.text_file_path_absolute = u"/tmp/plain.txt"
 #   task.sync_map_file_path_absolute = u"/tmp/syncmap.json"
    gateway=os.environ.get('gateway', '172.17.141.197:8080')
    broker = os.environ.get('broker', '172.17.141.197:1883')
    brokerport = os.environ.get('brokerport', '32332')
    topic = os.environ.get('topic', 'aeneas')
    file = requests.post("http://"+gateway+"/function/getobject",data="p001.xhtml")
    save_file("p001.xhtml",file.content)
#    with open("/tmp/p001.xhtml", "wb") as out_file:
#      out_file.write(file.content)
#    with open("/tmp/a.wav", "wb") as out_file:
#      out_file.write(req)
    ExecuteTaskCLI(use_sys=False).run(arguments=[None, u"/tmp/a.wav",u"/tmp/p001.xhtml",
    u"task_language=eng|is_text_type=plain|os_task_file_format=json",
    u"/tmp/syncmap.json"])
    f = open("/tmp/syncmap.json")
    output_data = f.read()
    payload = bytes(output_data)
    publish.single(topic, payload, hostname=broker,port=brokerport)
    return "Success"
