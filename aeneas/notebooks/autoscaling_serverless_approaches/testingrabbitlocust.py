from locust import User, TaskSet, events, task, between
import paho.mqtt.client as mqtt
import time
import random
import logging
import pika
from datetime import datetime
import datetime as dt
import logging
import multiprocessing
import os
import threading

from locust import events
import pika
from pika.exceptions import AMQPError
COUNTClient = 0
#broker_address="broker.mqttdashboard.com"
RABBITMQ_CONNECTION = 'amqp://guest:guest@172.17.141.197:5672'
roker_address="172.17.141.197"  # The server ip Address , The actual pressure measurement shall be based on mqtt Reality ip Make changes
REQUEST_TYPE = 'MQTT'
PUBLISH_TIMEOUT = 10000 # Timeout time
init =""
device=""

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
                '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

def fire_locust_success(**kwargs):
    events.request_success.fire(**kwargs)

def increment():
    global COUNTClient
    COUNTClient = COUNTClient+1

def time_delta(t1, t2):
    return int((t2 - t1)*1000)

class Message(object):
    def __init__(self, type, qos, topic, payload, start_time, timeout, name):
        self.type = type,
        self.qos = qos,
        self.topic = topic
        self.payload = payload
        self.start_time = start_time
        self.timeout = timeout
        self.name = name

class PublishTask(TaskSet):
    def on_start(self):
        params = pika.URLParameters(RABBITMQ_CONNECTION)
        self._connection = pika.BlockingConnection(params)
        self._channel = self._connection.channel()
        self._connected = True

    def close_channel(self):
        if self._channel is not None:
            LOGGER.info('Closing the channel')
            self._channel.close()

    def close_connection(self):
        if self._connection is not None:
            LOGGER.info('Closing connection')
            self._connection.close()

    def disconnect(self):
        self.close_channel()
        self.close_connection()
        self._connected = False

    @task(1)
    def task_pub(self):

        self.start_time = time.time()
        intime = dt.datetime.now()
        file_object = open('input_data.csv', 'a')
        file_object.write("%r\n" %str(intime))
        file_object.close()
        topic = "aeneas2"  # Subject name , It can be modified as needed
        f = open("p001.mp3", "rb")
        imagestring = f.read()
        f.close()
        payload = bytearray(imagestring)
        params = pika.URLParameters(RABBITMQ_CONNECTION)
        _connection = pika.BlockingConnection(params)
        _channel = _connection.channel()
        f = open("p001.mp3", "rb")
        imagestring = f.read()
        f.close()
        payload = bytes(imagestring) 
        try:
            watch = StopWatch()
            watch.start()
            self._channel.basic_publish('Dex', 'aeneas', payload)
            watch.stop()
        except AMQPError as e:
            watch.stop()
            events.request_failure.fire(
                    request_type="BASIC_PUBLISH",
                    name="test.message",
                    response_time=watch.elapsed_time(),
                    exception=e,
                )
        else:
            events.request_success.fire(
                    request_type="BASIC_PUBLISH",
                    name="test.message",
                    response_time=watch.elapsed_time(),
                    response_length=0
                )

        time.sleep(5)

    wait_time = between(0.5, 10)
class StopWatch():
    def start(self):
        self._start = datetime.now()

    def stop(self):
        self._end = datetime.now()

    def elapsed_time(self):
        timedelta = self._end - self._start
        return timedelta.total_seconds() * 1000
class MQTTLocust(User):
    tasks = {PublishTask}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        increment()
        client_name = "Device - " + str(COUNTClient)
      #  self.client = mqtt.Client(client_name)
       # self.client.on_connect = self.on_connect
      #  self.client.on_disconnect = self.on_disconnect
     #   self.client.on_publish = self.on_publish
   #     self.client.pubmessage  = {}

    def on_connect(client, userdata, flags, rc, props=None):
         fire_locust_success(
            request_type=REQUEST_TYPE,
            name='connect',
            response_time=0,
            response_length=0
            )

    def on_disconnect(client, userdata,rc,props=None):
        print("Disconnected result code "+str(rc))

    def on_publish(self, client, userdata, mid):
        end_time = time.time()
        message = client.pubmessage.pop(mid, None)
        total_time =  time_delta(message.start_time, end_time)
        fire_locust_success(
            request_type=REQUEST_TYPE,
            name=str(self.client._client_id),
            response_time=total_time,
            response_length=len(message.payload)
            )