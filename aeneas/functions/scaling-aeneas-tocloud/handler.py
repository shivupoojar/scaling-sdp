from minio import Minio
import json
from random import randrange
import os
import time 
def handle(req):
     minio = os.getenv("minio",'172.17.141.197:9001')
     accesskey = os.getenv("access_key",'minio')
     secretkey = os.getenv("secret_key",'minio123')
     mc = Minio(minio,access_key=accesskey,secret_key=secretkey,secure=False)
     res = json.loads(req)
     json_file = json.dumps(res)
     f = open("/tmp/dict.json","w")
     f.write(json_file)
     f.close()
     mc.fput_object('aeneas-output',str(time.time_ns())+'.json','/tmp/dict.json')
     return "Success"

